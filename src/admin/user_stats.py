import re
from datetime import datetime, timedelta, timezone
from typing import NamedTuple, Optional

from sqlalchemy import func

from src import db
from src.models.data import Data

HIGH_HOURLY_RATE = 1200
MANY_DEVICES = 8
EXPECTED_USERNAME = re.compile(r"^[A-Za-z0-9_.-]{1,32}$")


class UserStats(NamedTuple):
    username: Optional[str]
    readings: int
    devices: int
    without_device: int
    first_seen: datetime
    last_seen: datetime
    last_24h: int
    last_hour: int

    @property
    def flags(self):
        """Hints about possible misuse, for the teacher to review."""
        return [
            label
            for label, raised in (
                ("high rate", self.last_hour >= HIGH_HOURLY_RATE),
                ("many devices", self.devices >= MANY_DEVICES),
                ("unusual username", not EXPECTED_USERNAME.match(self.username or "")),
                ("missing device_id", self.without_device > 0),
            )
            if raised
        ]


def _windows(now):
    now = now or datetime.now(timezone.utc)
    return now - timedelta(hours=24), now - timedelta(hours=1)


def all_users(now=None):
    day_ago, hour_ago = _windows(now)
    count = func.count(Data.id)
    rows = db.session.query(
        Data.username,
        count,
        func.count(func.distinct(Data.device_id)),
        count.filter(Data.device_id.is_(None)),
        func.min(Data.time_created),
        func.max(Data.time_created),
        count.filter(Data.time_created >= day_ago),
        count.filter(Data.time_created >= hour_ago),
    ).group_by(Data.username).order_by(count.desc(), Data.username).all()
    return [UserStats(*row) for row in rows]


def devices_for(username):
    return db.session.query(
        Data.device_id, func.count(Data.id), func.max(Data.time_created)
    ).filter(Data.username == username).group_by(Data.device_id).order_by(
        func.max(Data.time_created).desc()
    ).all()


def recent_readings(username, limit=20):
    return Data.query.filter_by(username=username).order_by(
        Data.time_created.desc(), Data.id.desc()
    ).limit(limit).all()

