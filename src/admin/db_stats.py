from datetime import datetime, timedelta, timezone

from sqlalchemy import func, text

from src import db
from src.models.data import Data

UNITS = ("B", "KB", "MB", "GB", "TB")


def human_bytes(count):
    size = float(count)
    for unit in UNITS[:-1]:
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} {UNITS[-1]}"


def overview():
    """Database size, per-table sizes and the data table's row count."""
    database_bytes = db.session.execute(
        text("SELECT pg_database_size(current_database())")
    ).scalar()
    tables = [
        {"name": name, "bytes": size}
        for name, size in db.session.execute(
            text(
                "SELECT relname, pg_total_relation_size(relid) FROM pg_stat_user_tables "
                "WHERE schemaname = 'public' ORDER BY 2 DESC"
            )
        )
    ]
    readings = db.session.query(func.count(Data.id)).scalar()
    data_bytes = next((t["bytes"] for t in tables if t["name"] == Data.__tablename__), 0)
    return {
        "database_bytes": database_bytes,
        "tables": tables,
        "readings": readings,
        "bytes_per_reading": data_bytes // readings if readings else None,
    }


def readings_per_day(days=14, now=None):
    now = now or datetime.now(timezone.utc)
    day = func.date(Data.time_created)
    return db.session.query(day, func.count(Data.id)).filter(
        Data.time_created >= now - timedelta(days=days)
    ).group_by(day).order_by(day).all()
