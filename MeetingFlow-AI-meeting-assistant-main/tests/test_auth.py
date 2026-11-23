
from models import User, Meeting
from extensions import db


def test_user_registration(client, app):
    response = client.post(
        "/register",
        data={
            "username": "Test User",
            "email": "test@example.com",
            "password": "testpassword123",
            "confirm_password": "testpassword123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Account created successfully" in response.data

    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()

        assert user is not None
        assert user.username == "Test User"
        assert user.check_password("testpassword123")
        assert user.password_hash != "testpassword123"


def test_login_and_logout(client, app):
    with app.app_context():
        user = User(username="Login User", email="login@example.com")
        user.set_password("testpassword123")

        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/login",
        data={
            "email": "login@example.com",
            "password": "testpassword123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Login User" in response.data

    response = client.post("/logout", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_invalid_login_is_rejected(client):
    response = client.post(
        "/login",
        data={
            "email": "wrong@example.com",
            "password": "wrongpassword",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_users_can_only_see_their_own_meetings(client, app):
    with app.app_context():
        first_user = User(
            username="First User",
            email="first@example.com",
        )
        first_user.set_password("password123")

        second_user = User(
            username="Second User",
            email="second@example.com",
        )
        second_user.set_password("password123")

        db.session.add_all([first_user, second_user])
        db.session.flush()

        db.session.add_all([
            Meeting(
                user_id=first_user.id,
                title="First User Private Meeting",
                transcript="First user's meeting transcript.",
            ),
            Meeting(
                user_id=second_user.id,
                title="Second User Private Meeting",
                transcript="Second user's meeting transcript.",
            ),
        ])

        db.session.commit()

    response = client.post(
        "/login",
        data={
            "email": "first@example.com",
            "password": "password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"First User Private Meeting" in response.data
    assert b"Second User Private Meeting" not in response.data
