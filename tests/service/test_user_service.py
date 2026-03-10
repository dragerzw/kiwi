import pytest
from sqlalchemy.exc import IntegrityError
import app.service.user_service as user_service
from app.models import User

def test_get_all_users_exception(db_session, monkeypatch):
    def raise_exception(*args, **kwargs):
        raise Exception("Database error")
    monkeypatch.setattr(user_service.db.session, 'query', raise_exception)
    with pytest.raises(Exception) as e:
        user_service.get_all_users()
    assert "Database error" in str(e.value)

def test_create_user(db_session):
    users_before = user_service.get_all_users()
    initial_count = len(users_before)
    user_service.create_user('test_user75', 'xxx', 'Test', 'User', 100.00)
    users_after = user_service.get_all_users()
    assert len(users_after) == initial_count + 1
    tests_user = user_service.get_user_by_username('test_user75')
    assert tests_user is not None
    assert tests_user.firstname == 'Test'
    assert tests_user.lastname == 'User'
    assert tests_user.balance == 100.00

def test_create_user_db_exception(db_session, monkeypatch):
    def raise_exception(*args, **kwargs):
        raise Exception("Database error")
    monkeypatch.setattr(user_service.db.session, 'add', raise_exception)
    with pytest.raises(Exception) as e:
        user_service.create_user('test_user76', 'xxx', 'Test', 'User', 100.00)
        db_session.flush()
    assert "Database error" in str(e.value)

def test_create_user_duplicate_username_raises(db_session):
    with pytest.raises(IntegrityError):
        user_service.create_user('admin', 'xxx', 'Admin', 'User', 100.00)
        db_session.flush()

def test_delete_user(db_session):
    users = user_service.get_all_users()
    initial_count = len(users)
    user_service.create_user('test_user77', 'xxx', 'Test', 'User', 150.00)
    users = user_service.get_all_users()
    assert len(users) == initial_count + 1
    user_service.delete_user('test_user77')
    users = user_service.get_all_users()
    assert len(users) == initial_count

def test_delete_user_db_exception(db_session, monkeypatch):
    user_service.create_user('test_user78', 'xxx', 'Test', 'User', 150.00)
    db_session.flush()
    def raise_exception(*args, **kwargs):
        raise Exception("Database error")
    monkeypatch.setattr(user_service.db.session, 'delete', raise_exception)
    with pytest.raises(Exception) as e:
        user_service.delete_user('test_user78')
        db_session.flush()
    assert "Database error" in str(e.value)

def test_delete_admin_user_raises(db_session):
    with pytest.raises(user_service.UnsupportedUserOperationError) as e:
        user_service.delete_user('admin')
    assert str(e.value) == "Cannot delete admin user"

def test_delete_nonexistent_user_raises(db_session):
    with pytest.raises(user_service.UnsupportedUserOperationError) as e:
        user_service.delete_user('nonexistent_user')
    assert "User with username nonexistent_user does not exist" in str(e.value)

def test_update_user_balance(db_session):
    admin = user_service.get_user_by_username('admin')
    assert admin is not None
    assert admin.balance == 1000.00
    user_service.update_user_balance('admin', 500.00)
    user = db_session.query(User).filter_by(username='admin').one()
    assert user.balance == 500.00

def test_update_nonexistent_user_balance_raises(db_session):
    with pytest.raises(user_service.UnsupportedUserOperationError) as e:
        user_service.update_user_balance('nonexistent_user', 300.00)
    assert "User with username nonexistent_user does not exist" in str(e.value)

def test_get_user_by_username(db_session):
    user = user_service.get_user_by_username('admin')
    assert user is not None
    assert user.username == 'admin'
    assert user.firstname == 'Admin'

def test_get_user_by_username_nonexistent(db_session):
    user = user_service.get_user_by_username('nonexistent_user')
    assert user is None

def test_get_user_by_username_empty_raises(db_session):
    with pytest.raises(user_service.UnsupportedUserOperationError) as e:
        user_service.get_user_by_username('')
    assert "Username cannot be empty" in str(e.value)

def test_get_user_by_username_db_exception(db_session, monkeypatch):
    def raise_exception(*args, **kwargs):
        raise Exception("Database error")
    monkeypatch.setattr(user_service.db.session, 'query', raise_exception)
    with pytest.raises(Exception) as e:
        user_service.get_user_by_username('admin')
    assert "Database error" in str(e.value)