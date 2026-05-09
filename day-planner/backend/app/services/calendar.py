"""Read-only Google and Microsoft calendar availability helpers."""

from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import httpx
from fastapi import HTTPException
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ExternalCalendarAccount, ExternalCalendarBlock
from app.settings import Settings, get_settings

GOOGLE_SCOPE = "https://www.googleapis.com/auth/calendar.freebusy"
MICROSOFT_SCOPE = "offline_access Calendars.Read User.Read"


def make_state(provider: str) -> str:
    signer = URLSafeTimedSerializer(get_settings().oauth_state_secret)
    return signer.dumps({"provider": provider})


def read_state(provider: str, state: str) -> None:
    signer = URLSafeTimedSerializer(get_settings().oauth_state_secret)
    try:
        payload = signer.loads(state, max_age=600)
    except SignatureExpired as exc:
        raise HTTPException(status_code=400, detail="OAuth state expired") from exc
    except BadSignature as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc
    if payload.get("provider") != provider:
        raise HTTPException(status_code=400, detail="OAuth state provider mismatch")


def google_authorization_url(settings: Settings) -> str:
    require_settings(settings.google_client_id, settings.google_redirect_uri, "Google")
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": make_state("google"),
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def microsoft_authorization_url(settings: Settings) -> str:
    require_settings(settings.microsoft_client_id, settings.microsoft_redirect_uri, "Microsoft")
    params = {
        "client_id": settings.microsoft_client_id,
        "redirect_uri": settings.microsoft_redirect_uri,
        "response_type": "code",
        "scope": MICROSOFT_SCOPE,
        "state": make_state("microsoft"),
    }
    tenant = settings.microsoft_tenant
    return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?{urlencode(params)}"


def exchange_google_code(db: Session, code: str) -> None:
    settings = get_settings()
    require_settings(settings.google_client_id, settings.google_client_secret, settings.google_redirect_uri, "Google")
    data = {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.google_redirect_uri,
    }
    token = post_token("https://oauth2.googleapis.com/token", data)
    email = fetch_google_email(token["access_token"])
    save_account(db, "google", token, email)


def exchange_microsoft_code(db: Session, code: str) -> None:
    settings = get_settings()
    require_settings(
        settings.microsoft_client_id,
        settings.microsoft_client_secret,
        settings.microsoft_redirect_uri,
        "Microsoft",
    )
    data = {
        "client_id": settings.microsoft_client_id,
        "client_secret": settings.microsoft_client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.microsoft_redirect_uri,
        "scope": MICROSOFT_SCOPE,
    }
    token = post_token(microsoft_token_url(settings), data)
    email = fetch_microsoft_email(token["access_token"])
    save_account(db, "microsoft", token, email)


def disconnect_provider(db: Session, provider: str) -> None:
    account = get_account(db, provider)
    if account is not None:
        db.delete(account)
        db.commit()


def list_external_blocks(db: Session, block_date: date) -> list[dict[str, Any]]:
    for provider in ("google", "microsoft"):
        account = get_account(db, provider)
        if account is None:
            continue
        if provider == "google":
            fetch_google_busy_blocks(db, account, block_date)
        else:
            fetch_microsoft_busy_blocks(db, account, block_date)

    blocks = db.scalars(
        select(ExternalCalendarBlock).where(
            ExternalCalendarBlock.date == block_date,
            ExternalCalendarBlock.hidden == False,  # noqa: E712
        )
    ).all()
    return [
        calendar_block_read(block)
        for block in sorted(blocks, key=lambda item: (item.start_minute, item.provider))
    ]


def fetch_google_busy_blocks(db: Session, account: ExternalCalendarAccount, block_date: date) -> list[dict[str, Any]]:
    account = refresh_if_needed(db, account)
    start, end = day_bounds(block_date)
    payload = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "timeZone": get_settings().timezone,
        "items": [{"id": "primary"}],
    }
    response = httpx.post(
        "https://www.googleapis.com/calendar/v3/freeBusy",
        headers={"Authorization": f"Bearer {account.access_token}"},
        json=payload,
        timeout=20,
    )
    handle_provider_error(response, "Google")
    busy = response.json().get("calendars", {}).get("primary", {}).get("busy", [])
    return [upsert_busy_block(db, "google", "primary", item["start"], item["end"], block_date) for item in busy]


def fetch_microsoft_busy_blocks(db: Session, account: ExternalCalendarAccount, block_date: date) -> list[dict[str, Any]]:
    account = refresh_if_needed(db, account)
    start, end = day_bounds(block_date)
    schedule_email = account.account_email or "me"
    payload = {
        "schedules": [schedule_email],
        "startTime": {"dateTime": start.replace(tzinfo=None).isoformat(), "timeZone": get_settings().timezone},
        "endTime": {"dateTime": end.replace(tzinfo=None).isoformat(), "timeZone": get_settings().timezone},
        "availabilityViewInterval": 15,
    }
    response = httpx.post(
        "https://graph.microsoft.com/v1.0/me/calendar/getSchedule",
        headers={"Authorization": f"Bearer {account.access_token}"},
        json=payload,
        timeout=20,
    )
    handle_provider_error(response, "Microsoft")
    items = response.json().get("value", [])
    schedule_items = items[0].get("scheduleItems", []) if items else []
    blocks = []
    for item in schedule_items:
        status = item.get("status", "busy")
        if status in {"free", "workingElsewhere"}:
            continue
        blocks.append(upsert_busy_block(db, "microsoft", schedule_email, item["start"]["dateTime"], item["end"]["dateTime"], block_date))
    return blocks


def refresh_if_needed(db: Session, account: ExternalCalendarAccount) -> ExternalCalendarAccount:
    if account.expires_at and account.expires_at.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc) + timedelta(minutes=2):
        return account
    if not account.refresh_token:
        raise HTTPException(status_code=401, detail=f"{account.provider} calendar must be reconnected")

    settings = get_settings()
    if account.provider == "google":
        data = {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "refresh_token": account.refresh_token,
            "grant_type": "refresh_token",
        }
        token = post_token("https://oauth2.googleapis.com/token", data)
    else:
        data = {
            "client_id": settings.microsoft_client_id,
            "client_secret": settings.microsoft_client_secret,
            "refresh_token": account.refresh_token,
            "grant_type": "refresh_token",
            "scope": MICROSOFT_SCOPE,
        }
        token = post_token(microsoft_token_url(settings), data)

    account.access_token = token["access_token"]
    account.refresh_token = token.get("refresh_token") or account.refresh_token
    account.expires_at = datetime.now(timezone.utc) + timedelta(seconds=token.get("expires_in", 3600))
    account.scope = token.get("scope", account.scope)
    db.commit()
    db.refresh(account)
    return account


def save_account(db: Session, provider: str, token: dict[str, Any], email: str | None) -> None:
    account = get_account(db, provider) or ExternalCalendarAccount(provider=provider, access_token="")
    account.account_email = email
    account.access_token = token["access_token"]
    account.refresh_token = token.get("refresh_token") or account.refresh_token
    account.expires_at = datetime.now(timezone.utc) + timedelta(seconds=token.get("expires_in", 3600))
    account.scope = token.get("scope")
    db.add(account)
    db.commit()


def get_account(db: Session, provider: str) -> ExternalCalendarAccount | None:
    return db.scalar(select(ExternalCalendarAccount).where(ExternalCalendarAccount.provider == provider))


def post_token(url: str, data: dict[str, Any]) -> dict[str, Any]:
    response = httpx.post(url, data=data, timeout=20)
    if response.status_code >= 400:
        raise HTTPException(status_code=401, detail="OAuth token exchange failed; reconnect the provider")
    return response.json()


def fetch_google_email(access_token: str) -> str | None:
    response = httpx.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={"Authorization": f"Bearer {access_token}"}, timeout=20)
    return response.json().get("email") if response.is_success else None


def fetch_microsoft_email(access_token: str) -> str | None:
    response = httpx.get("https://graph.microsoft.com/v1.0/me?$select=mail,userPrincipalName", headers={"Authorization": f"Bearer {access_token}"}, timeout=20)
    if not response.is_success:
        return None
    data = response.json()
    return data.get("mail") or data.get("userPrincipalName")


def upsert_busy_block(
    db: Session,
    provider: str,
    calendar_id: str | None,
    start_text: str,
    end_text: str,
    block_date: date,
) -> dict[str, Any]:
    start, end = clip_to_day(block_date, parse_provider_datetime(start_text), parse_provider_datetime(end_text))
    external_event_id = f"{provider}:{calendar_id or 'calendar'}:{block_date.isoformat()}:{start}:{end}"
    block = db.scalar(
        select(ExternalCalendarBlock).where(
            ExternalCalendarBlock.provider == provider,
            ExternalCalendarBlock.external_event_id == external_event_id,
        )
    )
    if block is None:
        block = ExternalCalendarBlock(
            provider=provider,
            external_calendar_id=calendar_id,
            external_event_id=external_event_id,
            date=block_date,
            start_minute=start,
            end_minute=end,
            title="Busy",
            busy_status="busy",
            last_synced_at=datetime.now(timezone.utc),
        )
    else:
        block.date = block_date
        block.start_minute = start
        block.end_minute = end
        block.last_synced_at = datetime.now(timezone.utc)
    db.add(block)
    db.commit()
    db.refresh(block)
    return calendar_block_read(block)


def calendar_block_read(block: ExternalCalendarBlock) -> dict[str, Any]:
    return {
        "id": block.id,
        "provider": block.provider,
        "date": block.date,
        "start_minute": block.start_minute,
        "end_minute": block.end_minute,
        "title": block.title,
        "busy_status": block.busy_status,
    }


def day_bounds(block_date: date) -> tuple[datetime, datetime]:
    tz = ZoneInfo(get_settings().timezone)
    start = datetime.combine(block_date, time.min, tzinfo=tz)
    return start, start + timedelta(days=1)


def parse_provider_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(get_settings().timezone))
    return parsed.astimezone(ZoneInfo(get_settings().timezone))


def clip_to_day(block_date: date, start: datetime, end: datetime) -> tuple[int, int]:
    day_start, day_end = day_bounds(block_date)
    clipped_start = max(start, day_start)
    clipped_end = min(end, day_end)
    return minutes_since_midnight(clipped_start), minutes_since_midnight(clipped_end)


def minutes_since_midnight(value: datetime) -> int:
    return value.hour * 60 + value.minute


def handle_provider_error(response: httpx.Response, provider_name: str) -> None:
    if response.is_success:
        return
    if response.status_code in {401, 403}:
        raise HTTPException(status_code=401, detail=f"{provider_name} calendar permissions failed; reconnect the provider")
    raise HTTPException(status_code=502, detail=f"{provider_name} calendar request failed")


def microsoft_token_url(settings: Settings) -> str:
    return f"https://login.microsoftonline.com/{settings.microsoft_tenant}/oauth2/v2.0/token"


def require_settings(*values: str | None, provider_name: str | None = None) -> None:
    label = provider_name or str(values[-1])
    setting_values = values[:-1] if provider_name is None else values
    if not all(setting_values):
        raise HTTPException(status_code=500, detail=f"{label} OAuth is not configured")
