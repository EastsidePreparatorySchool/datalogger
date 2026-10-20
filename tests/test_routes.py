import json


def add_reading(client, **params):
    return client.post("/api/data/jbriggs/add", query_string=params)


def test_home_responds(client):
    assert client.get("/").data == b"helloflask"


def test_added_reading_is_returned_for_its_device(client):
    add_reading(client, device_id="jb", temperature="27.0")

    records = json.loads(client.get("/api/data/jbriggs/jb").data)

    assert [(r["device_id"], r["temperature"], r["username"]) for r in records] == [
        ("jb", 27.0, "jbriggs")
    ]


def test_username_comes_from_the_url_not_the_payload(client):
    add_reading(client, device_id="jb", username="someone_else")

    records = json.loads(client.get("/api/data/jbriggs/jb").data)

    assert records[0]["username"] == "jbriggs"


def test_readings_are_filtered_by_phase(client):
    add_reading(client, device_id="jb", phase="test1")
    add_reading(client, device_id="jb", phase="test2")

    records = json.loads(client.get("/api/data/jbriggs/jb/test1").data)

    assert [r["phase"] for r in records] == ["test1"]


def test_keyed_readings_are_found_by_key(client):
    add_reading(client, device_id="jb", string1="test", key="1000")

    records = json.loads(client.get("/api/data/jbriggs/jb/test/1000").data)

    assert [r["key"] for r in records] == ["1000"]
