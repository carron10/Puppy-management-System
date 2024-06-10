from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, DateTime, Column, Integer, \
    String, ForeignKey, Text,ForeignKeyConstraint
from flask_security import UserMixin, RoleMixin,SQLAlchemyUserDatastore
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm import relationship, backref
from dataclasses import dataclass
from sqlalchemy.sql import func
from flask_security.utils import hash_password
from sqlalchemy.ext.declarative import declared_attr
from flask import Flask
db = SQLAlchemy()





TABLE_PREFIX="puppyman_"
class MyModel(db.Model):
  __abstract__ = True
  time_created = Column(DateTime(timezone=True), server_default=func.now())
  time_updated = Column(DateTime(timezone=True), onupdate=func.now())
  # Use @declared_attr to dynamically set the table name with prefix
  @declared_attr
  def __tablename__(cls):
    return f"{TABLE_PREFIX}{cls.__name__}".lower()


# Define models

#user roles table
roles_users = db.Table(
    f'{TABLE_PREFIX}roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey(f'{TABLE_PREFIX}user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey(f'{TABLE_PREFIX}role.id'))
)

# Role Model
class Role(MyModel, RoleMixin):
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))


# User Model
class User(MyModel, UserMixin,SerializerMixin):
    """
    To store user data
    """
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    username = Column(String(255))
    avatar = Column(
        String(255), default="/img/istockphoto-1698148398-612x612.jpg")
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
    roles = relationship('Role', secondary=f'{TABLE_PREFIX}roles_users',
                         backref=backref('users', lazy='dynamic'))
    fs_uniquifier = Column(String(64), unique=True, nullable=False)
    adult_dogs=relationship('PuppyAdult',backref='user',uselist=False)
   

class PuppyAdult(MyModel,SerializerMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String,unique=True,nullable=False)
    breed=Column(String,nullable=False)
    weight_in_grams=Column(Integer)
    num_litters=Column(Integer,default=1) #Current number of litters
    avg_litters=Column(Integer,default=1) #avg number of litres
    puppies = relationship("Puppy",back_populates="parent",cascade="all, delete-orphan")
    user_id= Column(
        Integer, ForeignKey(column=User.id),nullable=False
    )




class Puppy(MyModel,SerializerMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String,unique=True,nullable=False)
    breed=Column(String,nullable=False)
    birth_weight=Column(Integer,nullable=False)
    birth_date=Column(DateTime(timezone=True))
    parent_id = Column(Integer, ForeignKey(column=PuppyAdult.id,ondelete='CASCADE'),nullable=False)
    parent = relationship("PuppyAdult",back_populates="puppies")
    records= relationship("PuppyRecords",back_populates="puppy",cascade="all, delete-orphan")
    sex=Column(String,nullable=False)

    
class PuppyRecords(MyModel,SerializerMixin):
    id = Column(Integer, primary_key=True)
    date=Column(DateTime(timezone=True),unique=True)
    temp_value= Column(Integer, nullable=False)
    weigth_value= Column(Integer, nullable=False)
    puppy_id= Column(Integer, ForeignKey(column=Puppy.id,ondelete='CASCADE'),nullable=False)
    puppy = relationship("Puppy",back_populates="records")

    
##Options, to store settings
class Options(MyModel, SerializerMixin):
    option_name = Column(String(100), nullable=False, unique=True,primary_key=True)
    option_value = Column(Text)
    
# Model/Table for notifications
class Notifications(MyModel, SerializerMixin):
    id = Column(Integer, primary_key=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Boolean(), default=False)
    message = Column(Text(), nullable=False)
    notification_category = Column(String(100), default="Alert")
    notification_icon = Column(String(30), default="bell")

    def __init__(self, message) -> None:
        self.message = message
        

# Build sample data into database
def build_sample_db(app:Flask, user_datastore:SQLAlchemyUserDatastore):
    """
    To generate sample data that can be used for testing and development
    """

    import random
    import string

    db.drop_all()
    db.create_all()
     
    #Generate sample Adults
    for i in range(10):
        pass
    
    #Generate puppies
    

    with app.app_context():
        user_role = Role(name="user")
        super_user_role = Role(name="Admin")
        db.session.add(user_role)
        db.session.add(super_user_role)
        db.session.commit()
        # Generate history data 
        user_datastore.create_user(
            first_name='Carron Muleya',
            email='carronmuleya10@gmail.com',
            password=hash_password('QKBhvm6qeUJuHQ@'),
            roles=[user_role, super_user_role]
        )
        db.session.commit()
    return
