from tests.conftest import ADMIN_PASSWORD, csrf_token_from


def log_in(client, password, token=None):
    token = token or csrf_token_from(client.get("/admin/login"))
    return client.post("/admin/login", data={"password": password, "csrf_token": token})


def test_admin_pages_redirect_to_login_when_logged_out(client):
    for path in ("/admin/", "/admin/sql", "/admin/users/jbriggs"):
        response = client.get(path)
        assert response.status_code == 302 and response.location.endswith("/admin/login")


def test_admin_is_hidden_when_no_password_is_configured(app, client):
    app.config["ADMIN_PASSWORD"] = None

    assert client.get("/admin/login").status_code == 404


def test_wrong_password_is_rejected(client):
    response = log_in(client, "nope")

    assert response.status_code == 401
    assert client.get("/admin/").status_code == 302


def test_right_password_opens_the_dashboard(client):
    assert log_in(client, ADMIN_PASSWORD).status_code == 302

    assert client.get("/admin/").status_code == 200


def test_login_without_a_csrf_token_is_refused(client):
    assert client.post("/admin/login", data={"password": ADMIN_PASSWORD}).status_code == 400


def test_logout_ends_the_session(admin_client):
    token = csrf_token_from(admin_client.get("/admin/"))
    admin_client.post("/admin/logout", data={"csrf_token": token})

    assert admin_client.get("/admin/").status_code == 302


def test_posts_with_a_bad_csrf_token_are_refused(admin_client):
    response = admin_client.post("/admin/sql", data={"sql": "select 1", "csrf_token": "forged"})

    assert response.status_code == 400
