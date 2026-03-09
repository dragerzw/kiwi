from typing import List

from sqlalchemy.exc import IntegrityError

from app.db import db
from app.models.User import User


class UnsupportedUserOperationError(Exception):
    pass


def get_user_by_username(username: str) -> User | None:
    if not username:
        raise UnsupportedUserOperationError('Username cannot be empty')
    return db.session.query(User).filter_by(username=username).one_or_none()


def get_all_users() -> List[User]:
    users = db.session.query(User).all()
    return users


def update_user_balance(username: str, new_balance: float):
    user = db.session.query(User).filter_by(username=username).one_or_none()
    if not user:
        raise UnsupportedUserOperationError(f'User with username {username} does not exist')
    user.balance = new_balance


def create_user(username: str, password: str, firstname: str, lastname: str, balance: float):
    db.session.add(
        User(
            username=username,
            password=password,
            firstname=firstname,
            lastname=lastname,
            balance=balance,
        )
    )


def delete_user(username: str):
    if username == 'admin':
        raise UnsupportedUserOperationError('Cannot delete admin user')
    if not username:
        raise UnsupportedUserOperationError('Username cannot be empty')
    try:
        user = db.session.query(User).filter_by(username=username).one_or_none()
        if not user:
            raise UnsupportedUserOperationError(f'User with username {username} does not exist')
        db.session.delete(user)
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        raise UnsupportedUserOperationError(f'Cannot delete user {username} due to existing dependencies')
