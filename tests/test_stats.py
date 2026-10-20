from datetime import datetime, timedelta, timezone

from src.data import stats
from tests.test_routes import add_reading


def test_summary_of_an_empty_database(client):
    assert stats.summary() == {
        "total_readings": 0,
        "readings_last_24h": 0,
        "users": 0,
        "devices": 0,
        "latest_reading": None,
    }


def test_summary_counts_readings_users_and_devices(client):
    add_reading(client, device_id="a")
    add_reading(client, device_id="a")
    add_reading(client, device_id="b")
    client.post("/api/data/other/add", query_string={"device_id": "c"})

    result = stats.summary()

    assert (result["total_readings"], result["users"], result["devices"]) == (4, 2, 3)


def test_readings_older_than_a_day_are_not_counted_as_recent(client):
    add_reading(client, device_id="a")
    two_days_on = datetime.now(timezone.utc) + timedelta(days=2)

    assert stats.summary(now=two_days_on)["readings_last_24h"] == 0
    assert stats.summary()["readings_last_24h"] == 1
