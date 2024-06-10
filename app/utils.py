from flask import current_app
from app.models import Puppy, PuppyAdult, db
from sqlalchemy.orm import Session
from flask_security import current_user
from datetime import datetime
import datetime as dt

def get_session():
    return db.session


def get_puppies_for_user(user_id, session: Session):
    # Query to get all puppies for a specific user
    puppies = session.query(Puppy).join(PuppyAdult).filter(
        PuppyAdult.user_id == user_id).all()
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


def get_adult_by_id(adult_id):
    with current_app.app_context():
        adult = PuppyAdult.query.filter_by(id=adult_id).first()
        return adult


def get_puppies_for_adult(adult_id: int):
    adult = get_adult_by_id(adult_id=adult_id)
    if adult:
        return adult.puppies
    return None

def calculate_puppy_age(puppy, on_date=None):
    """
    Calculate the age of a puppy.

    :param puppy: The puppy instance.
    :param on_date: The date on which to calculate the age. If None, use the current date.
    :return: The age of the puppy in days.
    """
    if on_date is None:
        on_date = datetime.now()
    else:
        if isinstance(on_date, str):
            on_date = datetime.strptime(on_date, '%Y-%m-%d')  # Adjust date format as needed
    
    if not puppy.birth_date:
        raise ValueError("Puppy birth date is not set.")
    
    age = on_date - puppy.birth_date
    return age.days