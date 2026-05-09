"""Read-only external calendar integration routes."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ExternalCalendarAccount, ExternalCalendarBlock
from app.schemas import ExternalCalendarBlockRead, ExternalCalendarBlockUpdate, ExternalCalendarStatus
from app.services.calendar import (
    disconnect_provider,
    exchange_google_code,
    exchange_microsoft_code,
    google_authorization_url,
    list_external_blocks,
    microsoft_authorization_url,
    read_state,
)
from app.settings import get_settings

router = APIRouter(tags=["external calendars"])


@router.get("/auth/google/start")
def start_google_auth():
    """Redirect to Google OAuth for read-only free/busy access."""

    return RedirectResponse(google_authorization_url(get_settings()))


@router.get("/auth/google/callback")
def google_callback(code: str | None = None, state: str | None = None, db: Session = Depends(get_db)):
    """Handle Google's OAuth callback and store tokens server-side."""

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth code or state")
    read_state("google", state)
    exchange_google_code(db, code)
    return RedirectResponse(f"{get_settings().frontend_url}/?calendar=google-connected")


@router.post("/auth/google/disconnect")
def disconnect_google(db: Session = Depends(get_db)):
    disconnect_provider(db, "google")
    return {"disconnected": True}


@router.get("/auth/microsoft/start")
def start_microsoft_auth():
    """Redirect to Microsoft OAuth for read-only calendar availability."""

    return RedirectResponse(microsoft_authorization_url(get_settings()))


@router.get("/auth/microsoft/callback")
def microsoft_callback(code: str | None = None, state: str | None = None, db: Session = Depends(get_db)):
    """Handle Microsoft's OAuth callback and store tokens server-side."""

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth code or state")
    read_state("microsoft", state)
    exchange_microsoft_code(db, code)
    return RedirectResponse(f"{get_settings().frontend_url}/?calendar=microsoft-connected")


@router.post("/auth/microsoft/disconnect")
def disconnect_microsoft(db: Session = Depends(get_db)):
    disconnect_provider(db, "microsoft")
    return {"disconnected": True}


@router.get("/external-calendars/status", response_model=list[ExternalCalendarStatus])
def external_calendar_status(db: Session = Depends(get_db)):
    """Return connection status for both supported providers."""

    accounts = {account.provider: account for account in db.query(ExternalCalendarAccount).all()}
    result = []
    for provider in ("google", "microsoft"):
        account = accounts.get(provider)
        result.append(
            ExternalCalendarStatus(
                provider=provider,
                connected=account is not None,
                account_email=account.account_email if account else None,
                scope=account.scope if account else None,
                expires_at=account.expires_at if account else None,
            )
        )
    return result


@router.get("/calendar-blocks/{block_date}", response_model=list[ExternalCalendarBlockRead])
def calendar_blocks(block_date: date, db: Session = Depends(get_db)):
    """Return merged read-only busy blocks from connected external calendars."""

    return list_external_blocks(db, block_date)


@router.patch("/calendar-blocks/{block_id}", response_model=ExternalCalendarBlockRead)
def update_calendar_block(block_id: int, payload: ExternalCalendarBlockUpdate, db: Session = Depends(get_db)):
    """Apply local context to an imported calendar block.

    The external event is not modified. This only changes the local planner's
    label or whether the interval should behave as blocking.
    """

    block = db.get(ExternalCalendarBlock, block_id)
    if block is None:
        raise HTTPException(status_code=404, detail="Calendar block not found")

    updates = payload.model_dump(exclude_unset=True)
    if "busy_status" in updates and updates["busy_status"] not in {"busy", "non_blocking"}:
        raise HTTPException(status_code=422, detail="busy_status must be busy or non_blocking")

    for field, value in updates.items():
        setattr(block, field, value)

    db.commit()
    db.refresh(block)
    return block


@router.delete("/calendar-blocks/{block_id}")
def delete_calendar_block(block_id: int, db: Session = Depends(get_db)):
    """Hide a calendar block locally without deleting anything from the provider."""

    block = db.get(ExternalCalendarBlock, block_id)
    if block is None:
        raise HTTPException(status_code=404, detail="Calendar block not found")
    block.hidden = True
    db.commit()
    return {"deleted": True}
