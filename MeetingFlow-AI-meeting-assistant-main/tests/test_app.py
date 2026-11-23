
def test_home_redirects_to_login(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_page(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b"Welcome back!" in response.data


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}
