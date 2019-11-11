import re

from flask import request, jsonify, url_for, abort

from app.models import db
from app.api import bp
from app.api.errors import bad_request
from app.models import User
from app.api.auth import token_auth


@bp.route('/users', methods=['POST'])
def create_user():
    '''注册一个新用户'''
    data = request.get_json()
    if not data:
        return bad_request('You must post JSON data.')

    message = {}
    if 'username' not in data or not data.get('username', None):
        message['username'] = 'Please provide a valid username.'
    pattern = '^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'
    if 'email' not in data or not re.match(pattern, data.get('email', None)):
        message['email'] = 'Please provide a valid email address.'
    if 'password' not in data or not data.get('password', None):
        message['password'] = 'Please provide a valid password.'
    if User.get_or_none(User.username==data.get('username', None)):
        message['username'] = 'Please use a different username.'
    if User.get_or_none(User.email==data.get('email', None)):
        message['email'] = 'Please use a different email address.'
    if message:
        return bad_request(message)

    user = User()
    user.from_dict(data, new_user=True)
    user.save()
    response = jsonify(user.to_dict())
    response.status_code = 201
    # HTTP协议要求201响应包含一个值为新资源URL的Location头部
    response.headers['Location'] = url_for('api.get_user', id=user.id)
    return response


@bp.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    '''返回一个用户'''
    user = User.get_or_none(id)
    if user:
        return jsonify(user.to_dict())
    else:
        abort(404)


@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.select(), page, per_page, 'api.get_users')
    return jsonify(data)


@bp.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.get_or_none(User.id==id)
    if not user:
        abort(404)
    data = request.get_json()
    if not data:
        return bad_request('You must post JSON data')

    message = {}
    if 'username' in data and not data.get('username', None):
        message['username'] = 'Please provide a valid username.'

    pattern = '^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'
    if 'email' in data and not re.match(pattern, data.get('email', None)):
        message['email'] = 'Please provide a valid email address.'

    if 'username' in data and data['username'] != user.username and \
        User.select().where(User.username==data['username']):
        message['username'] = 'Please use a different username.'

    if 'email' in data and data['email'] !=user.email and \
        User.select().where(User.email==data['email']):
        message['email'] = 'Please use a different email address.'

    if message:
        return bad_request(message)

    user.from_dict(data, new_user=False)
    user.save()
    return jsonify(user.to_dict())