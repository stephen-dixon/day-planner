"""Temporary schema compatibility helpers before Alembic is introduced."""

from sqlalchemy import Engine, inspect, text


def ensure_sqlite_schema(engine: Engine) -> None:
    """Add new prototype columns to an existing local SQLite database.

    `Base.metadata.create_all()` creates missing tables, but SQLite will not add
    columns to existing tables. This keeps the early prototype usable until real
    Alembic migrations are added.
    """

    inspector = inspect(engine)
    if "tasks" not in inspector.get_table_names():
        return

    task_columns = {column["name"] for column in inspector.get_columns("tasks")}
    task_columns_to_add = {
        "due_date": "DATE",
        "planned_date": "DATE",
        "project_id": "INTEGER",
        "milestone_id": "INTEGER",
        "is_recurring": "BOOLEAN DEFAULT 0 NOT NULL",
        "recurrence_type": "VARCHAR(40)",
        "recurrence_interval_days": "INTEGER",
        "recurrence_weekdays_json": "TEXT",
        "recurrence_min_days": "INTEGER",
        "recurrence_max_days": "INTEGER",
        "is_habit": "BOOLEAN DEFAULT 0 NOT NULL",
    }

    with engine.begin() as connection:
        for column_name, column_type in task_columns_to_add.items():
            if column_name not in task_columns:
                connection.execute(text(f"ALTER TABLE tasks ADD COLUMN {column_name} {column_type}"))

        if "external_calendar_blocks" in inspector.get_table_names():
            block_columns = {column["name"] for column in inspector.get_columns("external_calendar_blocks")}
            if "hidden" not in block_columns:
                connection.execute(text("ALTER TABLE external_calendar_blocks ADD COLUMN hidden BOOLEAN DEFAULT 0 NOT NULL"))
