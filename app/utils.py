from typing import List
from flask import current_app
from app.models import Puppy, PuppyAdult, db, Recommendation, PuppyRecords, User, Notifications, UserAction, PuppyMeta
from sqlalchemy.orm import Session
from flask_security import current_user
from datetime import datetime, timedelta
import datetime as dt
from dateutil.rrule import MO
from dateutil.relativedelta import relativedelta
import pickle
from flask import current_app
import pandas as pd
import numpy as np
import logging
from flask_mailman import Mail, EmailMessage


def get_session():
    return db.session


def get_puppies_for_user(user_id, limit=None):
    # Query to get all puppies for a specific user
    session = get_session()
    if limit:
        puppies = session.query(Puppy).join(PuppyAdult).filter(
            PuppyAdult.user_id == user_id).limit(limit).all()
    else:
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


def calculate_puppy_age(puppy, on_date: datetime = None):
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
            # Adjust date format as needed
            on_date = datetime.strptime(on_date, '%Y-%m-%d')

    if not puppy.birth_date:
        raise ValueError("Puppy birth date is not set.")

    age = on_date - puppy.birth_date
    return age.days


##########################################
#  FUNCTIONS TO HANDLE ML RECOMMENDATIONS#
##########################################
ml_model = None

# Load the model from file
with open("ml/puppy_management_system_random_forest_model.pkl", 'rb') as fl:
    ml_model = pickle.load(fl)

# Load the health category from file
with open("ml/health_indicator_categories.pkl", 'rb') as fl:
    health_categories = pickle.load(fl)


def get_health_cat_code(health) -> int:
    """get health indicator category code from categories

    Args:
       health (_type_): indicator to get the code for

    Returns:
        int: indicator code
    """
    crop_code = health_categories.cat.codes[health_categories ==
                                            health].iloc[0]
    return crop_code


def get_health_name(code):
    health = health_categories.cat.categories[code]
    return health


def ml_model_predict(data: pd.DataFrame):
    """Predict given the data and return the prediction

    Args:
        data (pd.DataFrame): data containing the features...
    Returns:
        array:array of predicted values
    """
    res = ml_model.predict(np.array(data))
    return res


def quick_check_recommendations_for_puppy(data):
    temp = data['Temperature'] if "Temperature" in data else None

    if temp:
        temp = int(temp)
        status, message = determine_puppy_health_from_temperature(
            determine_week(int(data['Day'])), temp)
        if status != "G":
            return status, message

    df = pd.DataFrame(data={
        "Day": [data['Day']],
        "Weight": [data['Weight']],
        "birth weight": [data['birth_weight']]
    }
    )
    recommendation = get_health_name(ml_model_predict(df)[0])
    message = "Please take your Puppy to Vertinary"
    if recommendation == "G":
        message = "All good! Your puppy is in good health"
    elif recommendation == "M":
        message = "Your Puppy needs monitoring."

    return recommendation, message


def get_records_for_dates(puppy: Puppy, start_date: datetime, end_date: datetime) -> List[PuppyRecords]:
    """
    Returns the records for the given puppy within the specified date range.

    :param puppy: The Puppy object for which to retrieve records.
    :param start_date: The start date of the range (inclusive).
    :param end_date: The end date of the range (inclusive).
    :return: List of PuppyRecords within the specified date range.
    """
    records = (PuppyRecords.query
               .filter_by(puppy_id=puppy.id)
               .filter(PuppyRecords.date >= start_date)
               .filter(PuppyRecords.date <= end_date)
               .order_by(PuppyRecords.date.asc())
               .all())
    return records


def get_record_for_date(puppy: Puppy, specific_date: datetime) -> PuppyRecords:
    """
    Returns the record for the given puppy on the specified date.

    :param puppy: The Puppy object for which to retrieve the record.
    :param specific_date: The specific date for which to retrieve the record.
    :return: The PuppyRecords object for the specified date, or None if no record exists.
    """
    record = (PuppyRecords.query
              .filter_by(puppy_id=puppy.id)
              .filter(db.func.date(PuppyRecords.date) == specific_date.date())
              .order_by(PuppyRecords.date.desc())
              .first())
    return record


def get_last_record(puppy: Puppy) -> PuppyRecords:
    """
    Returns the last record for the given puppy, ordered by date.
    """
    last_record = (PuppyRecords.query
                   .filter_by(puppy_id=puppy.id)
                   .order_by(PuppyRecords.date.desc())
                   .first())
    return last_record


def get_today_record(puppy: Puppy) -> PuppyRecords:
    """
    Returns the last record added today for the given puppy.
    """
    today = datetime.today().date()
    today_record = (PuppyRecords.query
                    .filter_by(puppy_id=puppy.id)
                    .filter(db.func.date(PuppyRecords.date) == today)
                    .order_by(PuppyRecords.date.desc())
                    .first())
    return today_record


def get_recommendations_for_puppy(puppy_id):
    """
    Returns recommendations for the given puppy that are unseesn=.

    :param puppy_id(int): The ID of the puppy for which to retrieve recommendations.
    :return: A list of Recommendation objects for the specified puppy.
    :rtype: list
    """
    recommendations = (Recommendation.query
                       .filter_by(puppy_id=puppy_id)
                       .filter_by(status=False)
                       .all())
    return recommendations


def get_recommendations2(puppy_id):
    return Recommendation.query.filter_by(puppy_id=puppy_id).filter_by(status=False).all()


def get_recommendations_for_date_and_puppy(puppy_id, specific_date):
    """
    Returns recommendations for the given specific date and puppy.

    :param puppy_id: The ID of the puppy for which to retrieve recommendations.
    :type puppy_id: int
    :param specific_date: The date for which to retrieve recommendations.
    :type specific_date: datetime.date
    :return: A list of Recommendation objects for the specified date and puppy.
    :rtype: list
    """
    recommendations = (Recommendation.query
                       .filter_by(puppy_id=puppy_id)
                       .filter_by(status=False)
                       .filter(Recommendation.timestamp == specific_date)
                       .order_by(Recommendation.timestamp.desc())
                       .all())
    return recommendations


def get_user_action_for_recommendation(user_id: int, recommendation_id: int) -> List[UserAction]:
    with current_app.app_context():
        try:
            user_action = (UserAction.query
                           .filter_by(user_id=user_id, recommendation_id=recommendation_id)
                           .order_by(UserAction.timestamp.desc())
                           .first())
            return user_action
        except Exception as e:
            logging.error(
                f"Error fetching user actions for user_id={user_id} and recommendation_id={recommendation_id}: {e}")
            return None


def get_user_meta(user_id):
    with current_app.app_context():
        puppy_meta = PuppyMeta.query.filter_by(user_id=user_id).all()
        results = []
        if len(puppy_meta) > 0:
            for meta in puppy_meta:
                results.append({
                    meta.meta_key: meta.meta_value
                })
        return results


def update_recommendations_for_puppy(puppy: Puppy, assume_today_is: datetime = datetime.today(), user=current_user):
    with current_app.app_context():
        # Get today status
        record = get_record_for_date(puppy, assume_today_is)
        today_status, message = quick_check_recommendations_for_puppy({
            "Day": calculate_puppy_age(puppy, assume_today_is),
            "Weight": record.temp_value,
            "birth_weight": record.weight_value
        })
        results=None
        # Get Yesterday Status
        age = calculate_puppy_age(puppy, assume_today_is)
        if age > 1:
            yesterday_date = assume_today_is - timedelta(days=1)
            yesterday_day_record = get_record_for_date(puppy, yesterday_date)
            if yesterday_day_record is None:

                puppy_recommendations = get_recommendations_for_puppy(
                    puppy.id)
                for reco in puppy_recommendations:
                    reco.status = True
                    db.session.add(reco)
                if today_status != "G":
                    recommendation = Recommendation(
                    msg=message, health_status=today_status, puppy_id=puppy.id, timestamp=assume_today_is)
                    db.session.add(recommendation)
                    results=recommendation
                    send_notification_mail("Puppy Recommendation",message,[user.email])


            else:
                yesterday_status, yesterday_message = quick_check_recommendations_for_puppy({
                    "Day": calculate_puppy_age(puppy, yesterday_date),
                    "Weight": yesterday_day_record.temp_value,
                    "birth_weight": yesterday_day_record.weight_value
                })
                # Check yesterday status
                if yesterday_status == "V":  # If yerstaday status was to take Puppy to Vertinary
                    yesterday_recommendations = get_recommendations_for_date_and_puppy(
                        puppy.id, specific_date=yesterday_date)
                    # Handle if yesterday's recommendation was to take to vet and check actions
                    als = get_recommendations2(puppy.id)
                    if today_status == "V":
                        user_actions = get_user_action_for_recommendation(
                            user_id=user.id, recommendation_id=yesterday_recommendations[0].id)
                        if not user_actions:
                            for reco in yesterday_recommendations:
                                reco.status = True
                                reco.follow_up_status = False
                                db.session.add(reco)
                            # Ask user if they took the puppy to vet and add review date
                            # Implement this logic based on your application flow
                            msg=f"Have you taken the <a href='/puppies/{puppy.id}' class='text-dark'>{puppy.name}</a> to vert?"
                            recommendation = Recommendation(timestamp=assume_today_is, health_status="V", tag="review_qtn", rank=1,
                                                            puppy_id=puppy.id, follow_up_status=True, msg=msg)
                            db.session.add(recommendation)
                            send_notification_mail("Puppy Recommendation",msg,[user.email])
                    elif today_status == "M":
                        # Implement actions for when puppy health is improving
                        for reco in yesterday_recommendations:
                            reco.status = True
                            reco.follow_up_status = False
                            db.session.add(reco)
                        msg=f"We have noticed that  <a href='/puppies/{puppy.id}' class='text-dark'>{puppy.name}</a> is getting better, keep on monitoring it!!"
                        recommendation = Recommendation(timestamp=assume_today_is, health_status="M", tag="keep_monitor", rank=1,
                                                        puppy_id=puppy.id, msg=msg)
                        send_notification_mail("Puppy Recommendation",msg,[user.email])
                        results=recommendation
                        db.session.add(recommendation)
                    else:
                        # Implement actions for when today's status is good
                        for reco in yesterday_recommendations:
                            reco.status = True
                            db.session.add(reco)
                elif yesterday_status == "M":  # If yerstaday status was to monitor the puppy
                    if today_status != "M":
                        yesterday_recommendations = get_recommendations_for_date_and_puppy(
                            puppy.id, specific_date=yesterday_date)
                        for reco in yesterday_recommendations:
                            reco.status = True
                            db.session.add(reco)
                        db.session.commit()
                    if today_status == "V":
                        # Add recommendation for severe health issues
                        recommendation = Recommendation(
                            msg=message, health_status=today_status, puppy_id=puppy.id, timestamp=assume_today_is)
                        send_notification_mail("Puppy Recommendation",message,user.email)
                        db.session.add(recommendation)
                        db.session.commit()
                        results=recommendation

        else:  # Yersterday status was good
            if today_status == "G":
                # Mark all recommendations of this Puppy as seen, and good
                puppy_recommendations = get_recommendations_for_puppy(
                    puppy.id)
                for reco in puppy_recommendations:
                    reco.status = True
                    db.session.add(reco)
            else:

                recommendation = Recommendation(
                    msg=message, health_status=today_status, puppy_id=puppy.id, timestamp=assume_today_is)
                send_notification_mail("Puppy Recommendation",message,user.email)
                results=recommendation
                db.session.add(recommendation)
        db.session.commit()
        return results


def get_recommendations(user=current_user,puppy_id=None) -> Recommendation:
    """Get recommendations from the database for a specific user

    Args:
        user: User object (default: current_user)

    Returns:
        list: List of recommendations
    """
    if puppy_id:
        return get_recommendations_for_puppy(puppy_id)
    
    puppies = get_puppies_for_user(user.id)
    recommendations = []
    for puppy in puppies:
        recommendation = get_recommendations_for_puppy(puppy.id)
        if recommendation:
            recommendations.extend(recommendation)
    return recommendations


def add_notification(msg: str):
    """Add a notification to

    Args:
        msg (str): msg to store
    """
    with current_app.app_context():
        note = Notifications(msg)
        db.session.add(note)
        db.session.commit()


def determine_puppy_health_from_temperature(age_weeks, temperature_celsius):
    """
  This function assesses the health status of a puppy based on its age and temperature.

  Args:
      age_weeks (int): The puppy's age in weeks.
      temperature_celsius (float): The puppy's body temperature in degrees Celsius.

  Returns:
      tuple: A tuple containing two elements:
          - health_status (str): The health status of the puppy ("G" - Good, "M" - Monitor, "V" - Veterinarian).
          - message (str): A message explaining the health status.
  """
    # Define the temperature ranges and corresponding messages
    normal_temp_range_1_2_weeks = (35.0, 37.2)
    normal_temp_range_2_4_weeks = (36.1, 37.8)
    slightly_high_range_2_4_weeks = (37.8, 39.2)
    slightly_high_range_1_2_weeks = (37.2, 39.2)
    mild_fever_range = (39.3, 39.7)
    moderate_fever_range = (39.8, 40.8)
    high_fever_threshold = 40.9
    slightly_lower_range_1_2_weeks = (34.0, 34.9)
    slightly_lower_range_2_4_weeks = (34.0, 36.0)
    hypothermia_threshold = 34.0

    # Define the messages
    messages = {
        "NORMAL": "A temperature of {:.1f} degrees Celsius is within the normal expected temperature range.",
        "SLIGHTLY_HIGH": "Puppy temperature is slightly higher than normal, monitor your puppy closely for any signs of discomfort or unusual behavior.",
        "MILD_FEVER": "Temperature indicates signs of mild fever. Monitor closely for any signs of discomfort or unusual behavior. Ensure hydration and comfort. If symptoms persist or worsen, consult a veterinarian.",
        "MODERATE_FEVER": "Temperature indicates a significant elevation in body temperature. Monitor closely for any signs of discomfort or unusual behavior. Ensure hydration and comfort. Consider consulting a veterinarian for further evaluation and guidance.",
        "HIGH_FEVER": "Urgent!!! Please consult a veterinarian urgently for assessment and appropriate treatment.",
        "SLIGHTLY_LOWER": "Puppy temperature is slightly lower than normal, monitor your puppy closely for any signs of discomfort or unusual behavior.",
        "HYPOTHERMIA": "Your puppy's temperature is below normal range indicating potential hypothermia. Ensure your puppy is kept warm and comfortable immediately. Wrap your puppy in a blanket and provide a warm environment. Seek veterinary attention promptly for further evaluation and treatment to prevent further complications."
    }

    # Determine the health status based on age and temperature
    if age_weeks <= 2:
        if normal_temp_range_1_2_weeks[0] <= temperature_celsius <= normal_temp_range_1_2_weeks[1]:
            status = "NORMAL"
        elif slightly_high_range_1_2_weeks[0] <= temperature_celsius <= slightly_high_range_1_2_weeks[1]:
            status = "SLIGHTLY_HIGH"
        elif mild_fever_range[0] <= temperature_celsius <= mild_fever_range[1]:
            status = "MILD_FEVER"
        elif moderate_fever_range[0] <= temperature_celsius <= moderate_fever_range[1]:
            status = "MODERATE_FEVER"
        elif temperature_celsius >= high_fever_threshold:
            status = "HIGH_FEVER"
        elif slightly_lower_range_1_2_weeks[0] <= temperature_celsius <= slightly_lower_range_1_2_weeks[1]:
            status = "SLIGHTLY_LOWER"
        else:
            status = "HYPOTHERMIA"
    elif 2 < age_weeks <= 4:
        if normal_temp_range_2_4_weeks[0] <= temperature_celsius <= normal_temp_range_2_4_weeks[1]:
            status = "NORMAL"
        elif slightly_high_range_2_4_weeks[0] <= temperature_celsius <= slightly_high_range_2_4_weeks[1]:
            status = "SLIGHTLY_HIGH"
        elif mild_fever_range[0] <= temperature_celsius <= mild_fever_range[1]:
            status = "MILD_FEVER"
        elif moderate_fever_range[0] <= temperature_celsius <= moderate_fever_range[1]:
            status = "MODERATE_FEVER"
        elif temperature_celsius >= high_fever_threshold:
            status = "HIGH_FEVER"
        elif slightly_lower_range_2_4_weeks[0] <= temperature_celsius <= slightly_lower_range_2_4_weeks[1]:
            status = "SLIGHTLY_LOWER"
        else:
            status = "HYPOTHERMIA"
    else:
        return "Invalid age range. Please provide an age between 1-4 weeks.", None

    indicator = "V"
    if status == "NORMAL":
        indicator = "G"
    elif status in ["SLIGHTLY_HIGH", "MILD FEVER", "SLIGHTLY_LOWER"]:
        indicator = "M"
    print(status, indicator)

    return indicator, messages[status].format(temperature_celsius)


def determine_week(day):
    """
    Determine the week number given a day in the range 1-21.

    Args:
        day (int): The day of the month (1-21).

    Returns:
        int: The week number (1-3) if the day is within the range 1-21.
        str: Error message if the day is outside the range 1-21.
    """
    if not 1 <= day <= 21:
        return "Invalid day. Please provide a day between 1 and 21."

    if 1 <= day <= 7:
        return 1
    elif 8 <= day <= 14:
        return 2
    elif 15 <= day <= 21:
        return 3
    else:
        return "Invalid day. Please provide a day between 1 and 21."


def check_missing_updates(puppy_id):
    """
    Check for missing daily updates for a puppy's weight and temperature 
    from birth until day 21.

    Args:
        puppy_id (int): The ID of the puppy to check.

    Returns:
        str: A message indicating any missing update dates.
    """
    # Retrieve the puppy by ID
    puppy = Puppy.query.filter_by(id=puppy_id).first()

    if not puppy:
        return "Puppy not found."

    birth_date = puppy.birth_date
    end_date = birth_date + timedelta(days=21)
    current_date = datetime.now()

    # Ensure we only check up to the current date if it's before the 21-day mark
    check_until_date = min(end_date, current_date)

    # Retrieve all records for the puppy
    records = PuppyRecords.query.filter_by(puppy_id=puppy_id).all()

    # Create a set of all dates with records
    recorded_dates = {record.date.date() for record in records}

    # Find all dates from birth_date to check_until_date
    missing_dates = []
    check_date = birth_date.date()

    while check_date <= check_until_date.date():
        if check_date not in recorded_dates:
            missing_dates.append(check_date)
        check_date += timedelta(days=1)

    if missing_dates:
        missing_dates_str = ', '.join(date.strftime(
            '%Y-%m-%d') for date in missing_dates)
        puppy_link=f'<a href="/puppies/{puppy.id}" class="text-primary">{puppy.name}</a>'
        return f"Missing updates for {puppy_link} on the following dates: {missing_dates_str}", missing_dates
    else:
        return "All updates are recorded.", None

def send_notification_mail(subject: str, notification_body: str, emails: list)->bool:
    """To send email to given emails,

    Args:
        subject (str): Email subject
        notification_body (str):Email body
        emails (list): list of emails to send to
    Returns:
        bool: whether the email was sent or not
    """
    if not isinstance(emails, list):
        emails = [emails]
    try:
        msg = EmailMessage(
            subject=subject,
            body=notification_body,
            to=emails,
            reply_to=['admin@tekon.co.zw']
        )
        msg.send()
        return True  # Return True if the email is sent successfully
    except Exception as e:
        print(f'An exception occurred: {e}')
        return False  # Return False if an exception occurs during the email sending process

# def check_follow_ups():
#     today = datetime.now().date()
#     follow_ups = Recommendation.query.filter(Recommendation.follow_up_date <= today, Recommendation.follow_up_status == True).all()

#     for follow_up in follow_ups:
#         puppy = Puppy.query.get(follow_up.puppy_id)
#         if not puppy:
#             continue

#         health_status = check_puppy_health(puppy)
#         if health_status != "G":
#             # Send a reminder to the user
#             user = User.query.get(follow_up.user_id)
#             send_reminder(user.email, f"Your puppy {puppy.name} needs a follow-up vet visit.")
#             # Update follow-up status
#             follow_up.follow_up_status = False
#             db.session.commit()
