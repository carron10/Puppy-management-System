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
from datetime import datetime,timedelta
import datetime as dt
import random
import string

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
    meta = relationship("PuppyMeta", back_populates="puppy", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="puppy", cascade="all, delete-orphan")
    def get_age(self,on_date=None):
        if on_date is None:
            on_date = datetime.now()
        else:
            if isinstance(on_date, str):
                on_date = datetime.strptime(on_date, '%Y-%m-%d')  # Adjust date format as needed

        if not  self.birth_date:
            return 0
    
        age = on_date - self.birth_date
        return age.days
class Recommendation(MyModel, SerializerMixin):
    id = Column(Integer, primary_key=True)
    msg = Column(Text(), nullable=False)
    health_status=Column(Text(), nullable=False)
    status = Column(Boolean(), default=False)  # True if the user has seen/acknowledged the recommendation
    tag = Column(String(50))
    rank = Column(Integer)  # Optional: Rank the recommendations (1 being most recommended)
    timestamp = Column(DateTime(timezone=True), server_default=datetime.now().strftime("%Y-%m-%dT%H:%M"))
    follow_up_date = Column(DateTime(timezone=True), nullable=True)  # Date for follow-up review
    follow_up_status = Column(Boolean(), default=False)  # Status of the follow-up
    puppy_id = Column(Integer, ForeignKey(Puppy.id, ondelete='CASCADE'), nullable=False)
    puppy = relationship("Puppy", back_populates="recommendations")
    

class PuppyMeta(MyModel,SerializerMixin):
    id = Column(Integer, primary_key=True)
    puppy_id = Column(Integer, ForeignKey(Puppy.id, ondelete='CASCADE'), nullable=False)
    puppy = relationship("Puppy", back_populates="meta")
    meta_key = Column(String, nullable=False) 
    meta_value= Column(String, nullable=False) 


class PuppyRecords(MyModel,SerializerMixin):
    id = Column(Integer, primary_key=True)
    date=Column(DateTime(timezone=True))
    temp_value= Column(Integer, nullable=False)
    weight_value= Column(Integer, nullable=False)
    puppy_id= Column(Integer, ForeignKey(column=Puppy.id,ondelete='CASCADE'),nullable=False)
    puppy = relationship("Puppy",back_populates="records")


class UserAction(MyModel, SerializerMixin):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    recommendation_id = Column(Integer, ForeignKey(Recommendation.id), nullable=False)
    action_taken = Column(String, nullable=False)  # Description of the action taken (e.g., "Took puppy to vet")
    timestamp = Column(DateTime(timezone=True), server_default=datetime.now().strftime("%Y-%m-%dT%H:%M"))
    review_date = Column(DateTime(timezone=True), nullable=True)  # Review date provided by the vet

    
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



def generate_puppy_records(puppy: Puppy,user):
    from app.utils import update_recommendations_for_puppy  
    today = datetime.now()
    diff_days = (today - puppy.birth_date).days
    # Skip any random day
    skip = random.choice([True, False])
    skip_day = 0
    if skip:
        skip_day = random.randint(1, diff_days)

    for day in range(diff_days + 1):  # Generate records for 0 to diff_days (inclusive)
        if skip and skip_day == day:
            continue
        
        date = puppy.birth_date + timedelta(days=day)
        weight = puppy.birth_weight + (day * random.randint(3, 30) * puppy.birth_weight)  # Adjust weight generation logic
        temp_value = random.uniform(35.0, 40.0)  # Adjust temperature range as needed

        # Create a PuppyRecords instance and add it to the session
        record = PuppyRecords(date=date, temp_value=temp_value, weight_value=weight, puppy_id=puppy.id)
        db.session.add(record)
        db.session.commit()
        # Update recommendations for the puppy based on the generated record
        update_recommendations_for_puppy(puppy, date,user)




# Build sample data into database
def build_sample_db(app:Flask, user_datastore:SQLAlchemyUserDatastore):
    """
    To generate sample data that can be used for testing and development
    """

    

    Notifications.query.delete()
    PuppyRecords.query.delete()
    Puppy.query.delete()
    PuppyAdult.query.delete()
    Recommendation.query.delete()
    db.session.commit()
    # db.drop_all()
    db.create_all()
    

    with app.app_context():
    # Check if roles already exist
        user_role = Role.query.filter_by(name="user").first()
        super_user_role = Role.query.filter_by(name="Admin").first()
    
    # Create roles if they do not exist
        if not user_role:
            user_role = Role(name="user")
            db.session.add(user_role)
        if not super_user_role:
            super_user_role = Role(name="Admin")
            db.session.add(super_user_role)
    
        db.session.commit()
    
        # Check if user already exists
        user = user_datastore.find_user(email='test@me.com')
    
        # Create user if it does not exist
        if not user:
            user=user_datastore.create_user(
                first_name='Test',
                email='test@me.com',
                password=hash_password('1234'),
                roles=[user_role, super_user_role]
            )
    
        db.session.commit()

        for i in range(3):
            num_litters=random.randint(2,4)
            adult=PuppyAdult(name=f"ParentAdult{i}",
                         weight_in_grams=random.randint(4000,8000),
                         num_litters=num_litters,
                         avg_litters=random.randint(2,4),
                         breed=random.choice(['German Sherpard']),
                         user_id=user.id
                         )
            db.session.add(adult)
            db.session.commit()
            for j in range(num_litters):
                birth_weight=random.randint(2,4)
                birth_day = random.randint(1, 21)
                today = datetime.today().date()
                birth_date = today - timedelta(days=birth_day)
                puppy=Puppy(name=f"TPestuppy{i}{j}",
                        parent_id=adult.id,
                        birth_weight=birth_weight,
                        birth_date=birth_date,
                        sex=random.choice(["Male","Female"]),
                        breed=random.choice(['German Sherpard'])
                        )
                db.session.add(puppy)
                db.session.commit()
                generate_puppy_records(puppy,user)
    return
