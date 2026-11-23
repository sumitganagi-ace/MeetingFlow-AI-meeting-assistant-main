
from app import create_app


def test_post_request_without_csrf_token_is_rejected(tmp_path):
    database_file = tmp_path / "csrf_test.db"

    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_file.as_posix()}",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": "csrf-test-secret-key",
        "WTF_CSRF_ENABLED": True,
    })

    client = app.test_client()

    response = client.post(
        "/login",
        data={
            "email": "test@example.com",
            "password": "testpassword",
        },
    )

    assert response.status_code == 400
