from flask import current_app
from models import Puppy,PuppyAdult,db
from sqlalchemy.orm import Session

def  get_session():
    return db.session

def get_puppies_for_user(user_id, session: Session):
    # Query to get all puppies for a specific user
    puppies = session.query(Puppy).join(PuppyAdult).filter(PuppyAdult.user_id == user_id).all()
    return puppies

def get_puppy_by_id(puppy_id: int, user_id: int):
    with current_app.app_context():
        session = get_session()  # Replace with your actual method to get a session
        # Query to get a specific puppy by ID and user ID
        puppy = session.query(Puppy).join(PuppyAdult).filter(
            Puppy.id == puppy_id,
            PuppyAdult.user_id == user_id
        ).first()
        return puppy

