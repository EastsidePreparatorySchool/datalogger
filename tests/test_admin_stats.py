from datetime import datetime, timedelta, timezone

import pytest

from src.admin import db_stats, user_stats
from tests.test_routes import add_reading


@pytest.mark.parametrize("count, expected", [
    (0, "0 B"), (1023, "1023 B"), (1024, "1.0 KB"), (5 * 1024**2, "5.0 MB"), (3 * 1024**3, "3.0 GB"),
])
def test_human_bytes(count, expected):
    assert db_stats.human_bytes(count) == expected


def test_overview_reports_size_tables_and_cost_per_reading(client):
    add_reading(client, device_id="a")

    overview = db_stats.overview()

    assert overview["database_bytes"] > 0
    assert "data" in [t["name"] for t in overview["tables"]]
    assert (overview["readings"], overview["bytes_per_reading"] > 0) == (1, True)


def test_overview_of_an_empty_database_has_no_per_reading_cost(client):
    assert db_stats.overview()["bytes_per_reading"] is None


def test_readings_per_day_groups_recent_readings(client):
    add_reading(client, device_id="a")
    add_reading(client, device_id="a")

    assert [count for _day, count in db_stats.readings_per_day()] == [2]


def test_readings_per_day_ignores_old_readings(client):
    add_reading(client, device_id="a")
    far_future = datetime.now(timezone.utc) + timedelta(days=30)

    assert db_stats.readings_per_day(now=far_future) == []


def test_all_users_summarises_each_username(client):
    add_reading(client, device_id="a")
    add_reading(client, device_id="b")
    add_reading(client, device_id="b")
    client.post("/api/data/other/add", query_string={"device_id": "z"})

    first, second = user_stats.all_users()

    assert (first.username, first.readings, first.devices, first.last_hour) == ("jbriggs", 3, 2, 3)
    assert (second.username, second.readings) == ("other", 1)


def test_old_readings_fall_out_of_the_recent_windows(client):
    add_reading(client, device_id="a")
    two_days_on = datetime.now(timezone.utc) + timedelta(days=2)

    (stats,) = user_stats.all_users(now=two_days_on)

    assert (stats.readings, stats.last_24h, stats.last_hour) == (1, 0, 0)


def make_stats(**overrides):
    base = dict(username="ok_user", readings=10, devices=1, without_device=0,
                first_seen=None, last_seen=None, last_24h=10, last_hour=10)
    return user_stats.UserStats(**{**base, **overrides})


def test_ordinary_users_raise_no_flags():
    assert make_stats().flags == []


@pytest.mark.parametrize("overrides, flag", [
    ({"last_hour": user_stats.HIGH_HOURLY_RATE}, "high rate"),
    ({"devices": user_stats.MANY_DEVICES}, "many devices"),
    ({"username": "has space"}, "unusual username"),
    ({"username": None}, "unusual username"),
    ({"without_device": 1}, "missing device_id"),
])
def test_flags(overrides, flag):
    assert make_stats(**overrides).flags == [flag]


def test_devices_and_recent_readings_for_a_user(client):
    add_reading(client, device_id="a", temperature="1")
    add_reading(client, device_id="b", temperature="2")

    assert sorted(d for d, _count, _last in user_stats.devices_for("jbriggs")) == ["a", "b"]
    assert [r.temperature for r in user_stats.recent_readings("jbriggs", limit=1)] == [2.0]


def test_dashboard_lists_users_with_flags(admin_client):
    admin_client.post("/api/data/bad name/add", query_string={"device_id": "a"})

    page = admin_client.get("/admin/").get_data(as_text=True)

    assert "bad name" in page and "unusual username" in page
