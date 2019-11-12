from flask import g
from flask_httpauth import HTTPBasicAuth
from flask_httpauth import HTTPTokenAuth

from app.models import User
from app.api.errors import error_response

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()


@basic_auth.verify_password
def verify_password(username, password):
    user = User.get_or_none(User.username==username)
    if not user:
        return False
    g.current_user = user
    return user.check_password(password)


@basic_auth.error_handler
def basic_auth_error():
    return error_response(401)


@token_auth.verify_token
def verify_token(token):
    g.current_user = User.verify_jwt(token) if token else None
    if g.current_user:
        g.current_user.ping()
        g.current_user.save()
    return g.current_user is not None


@token_auth.error_handler
def token_auth_error():
    return error_response(401)