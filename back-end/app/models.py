from werkzeug.security import generate_password_hash, check_password_hash
import math
from datetime import datetime, timedelta
import os
import base64
from hashlib import md5

from flask import url_for, current_app
from flask_peewee.auth import BaseUser
import jwt
from peewee import Model, CharField, TextField, PostgresqlDatabase, DateTimeField
#from flask_peewee.db import Database
#from flask_peewee.auth import Auth
#import app.app_create

#db = Database(app)
#auth = Auth(app, db)
db = PostgresqlDatabase('blog', user='postgres', host='localhost', password='postgres', port=5432)


class BaseModel(Model):
    class Meta:
        database = db


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page)
        resources.total_pages = math.ceil(resources.count()/per_page)
        resources.has_next = 1 if page < resources.total_pages else 0
        resources.has_prev = 1 if page > 1 else 0
        data = {
            'items': [item.to_dict() for item in resources],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.total_pages,
                'total_items': resources.count()
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data


class User(BaseModel, BaseUser, PaginatedAPIMixin):
    username = CharField()
    email = CharField()
    password_hash = CharField()
    name = CharField()
    location = CharField()
    about_me = TextField()
    member_since = DateTimeField(default=datetime.utcnow())
    last_seen = DateTimeField(default=datetime.utcnow())

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://cn.gravatar.com/avatar/{}?d=http://image.antns.com/uploads/20180904/13/1536039999-UcBCsxtXgM.jpg&s={}'.format(digest, size)


    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'location': self.location,
            'about_me': self.about_me,
            'member_since': self.member_since.isoformat() + 'Z',
            'last_seen': self.last_seen.isoformat() + 'Z',
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'avatar': self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'name', 'location', 'about_me']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def ping(self):
        self.last_seen = datetime.utcnow()
        self.save()

    def get_jwt(self, expires_in=3600):
        now = datetime.utcnow()
        payload = {
            'user_id': self.id,
            'name': self.name if self.name else self.username,
            'exp': now + timedelta(seconds=expires_in),
            'iat': now
        }
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_jwt(token):
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256'])
        except (jwt.exceptions.ExpiredSignatureError, jwt.exceptions.InvalidSignatureError) as e:
            return None
        return User.get(payload.get('user_id'))