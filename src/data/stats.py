from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from src import db
from src.models.data import Data


def summary(now=None):
    """Headline numbers about the stored readings, for the home page."""
    now = now or datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)
    total, users, devices, latest = db.session.query(
        func.count(Data.id),
        func.count(func.distinct(Data.username)),
        func.count(func.distinct(Data.device_id)),
        func.max(Data.time_created),
    ).one()
    last_24h = Data.query.filter(Data.time_created >= day_ago).count()
    return {
        "total_readings": total,
        "readings_last_24h": last_24h,
        "users": users,
        "devices": devices,
        "latest_reading": latest,
    }
