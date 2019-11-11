from werkzeug.security import generate_password_hash, check_password_hash
import math
from datetime import datetime, timedelta
import os
import base64

from flask import url_for
from flask_peewee.auth import BaseUser
from peewee import Model, CharField, PostgresqlDatabase, DateTimeField
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
        total_pages = math.ceil(resources.count()/per_page)
        resources.has_next = 1 if page < total_pages else 0
        resources.has_prev = 1 if page > 1 else 0
        data = {
            'items': [item.to_dict() for item in resources],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
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
    token = CharField(index=True, unique=True)
    token_expiration = DateTimeField()

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        self.save()
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.get_or_none(User.token==token)
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            '_links': {
                'self': url_for('api.get_user', id=self.id)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

