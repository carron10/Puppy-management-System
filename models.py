from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, DateTime, Column, Integer, \
    String, ForeignKey, Text
from flask_security import UserMixin, RoleMixin
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm import relationship, backref
from dataclasses import dataclass
from sqlalchemy.sql import func
from flask_security.utils import hash_password

db = SQLAlchemy()



# Define models

#user roles table
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

# Role Model
class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))


# User Model
class User(db.Model, UserMixin,SerializerMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    username = Column(String(255))
    avatar = Column(
        String(255), default="/img/avatars/istockphoto-1337144146-612x612.jpg")
    first_name = Column(String(255))
    last_name = Column(String(255))
    password = Column(String(255),nullable=False)
    last_login_at = Column(DateTime())
    current_login_at = Column(DateTime())
    last_login_ip = Column(String(100))
    current_login_ip = Column(String(100))
    login_count = Column(Integer)
    active = Column(Boolean())
    confirmed_at = Column(DateTime())
    # serialize_only=('roles.id',)
    roles = relationship('Role', secondary='roles_users',
                         backref=backref('users', lazy='dynamic'))
    fs_uniquifier = Column(String(64), unique=True, nullable=False)
   