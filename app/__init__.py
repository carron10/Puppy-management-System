import json
import os
import pickle
import time
import datetime
import numpy as np
import pandas as pd
import psycopg2
from flask import (Blueprint, Flask, Response, current_app, jsonify, redirect,
                   render_template, request, send_from_directory, url_for)
from flask_security import (Security, SQLAlchemyUserDatastore, current_user,
                            login_required)
from flask_security.forms import RegisterForm, Required, StringField
from flask_security.utils import hash_password
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from app.models import Role, User, db,Puppy,PuppyAdult,build_sample_db,PuppyRecords,Recommendation,UserAction,Notifications
from app.utils import (get_puppies_for_user,
                       get_puppy_by_id,calculate_puppy_age,
                       quick_check_recommendations_for_puppy,
                       check_missing_updates, update_recommendations_for_puppy,
                       get_recommendations
                       )
from app.routes import puppy_bp


app = Flask(__name__,static_url_path='', static_folder='static', template_folder='templates')
app.config.from_pyfile('config.py')
db.init_app(app)
app.register_blueprint(puppy_bp)


# Security
user_datastore = SQLAlchemyUserDatastore(db, User,Role)

# extend fields for registration form
class ExtendedRegisterForm(RegisterForm):
    first_name = StringField("First Name", [Required()])
    last_name = StringField("Last Name", [Required()])

# security
security = Security(app, user_datastore, register_form=ExtendedRegisterForm)


def set_notifications():
    puppies = get_puppies_for_user(current_user.id)
    data = {}
    missing_records=[]
    for puppy in puppies:
        missing_updates_message,missing_dates = check_missing_updates(puppy.id)
        if(missing_dates is None):
            continue
        note=Notifications(message=missing_updates_message,
                           notification_category="Warning!",
                           notification_icon="warning"
                           )
        missing_records.append(note)
        # missing_records.append({
        #     'puppy_id': puppy.id,
        #     'puppy_name': puppy.name,
        #     'missing_updates': missing_updates_message
        # })
    data["total_notifications"]=len(missing_records)
    data['notifications']=missing_records
    return data


@app.route("/")
@app.route("/index.html")
@login_required
def index():
    data=set_notifications()
    data['puppies']=get_puppies_for_user(current_user.id,5)
    return render_template('index.html',
                           page="index",**data)

@app.route("/puppies/<id>")
@login_required
def get_puppy_details(id):
    data=set_notifications()
    puppy=Puppy.query.filter_by(id=id).first()
    if not puppy:
        puppy=Puppy()
    data['puppy']=puppy
    return render_template("view_puppy.html",**data)

@app.route("/puppies")
@login_required
def puppies_page():
    data=set_notifications()
    data['puppies']=get_puppies()
    data['adults']=get_adults()
    return render_template('puppies.html',**data,page="puppies")

@app.route("/adults")
@login_required
def adults():
    data=set_notifications()
    data['adults']=get_adults()
    return render_template('adults.html',page="adults",**data)

@app.route("/adults/<id>")
@login_required
def view_adult_details(id):
    data=set_notifications()
    puppy_adult=PuppyAdult.query.filter_by(id=id).first()
    if not puppy_adult:
        puppy_adult=PuppyAdult()
    data['puppy_adult']=puppy_adult
    data['puppies']=puppy_adult.puppies
    return render_template("view_adult.html",**data)

@app.route("/recommendations")
@login_required
def recommendations():
    data=set_notifications()
    data['recommendations']=get_recommendations(current_user)
    return render_template('recommendations.html',page="recommendations",**data)


#######################
#Adults CRUD-methodds #
#######################
@app.route("/api/adults",methods=["GET"])
@login_required
def get_adults():
    id=request.args.get("id")
    if id:
        parent=PuppyAdult.query.filter_by(id=id,user=current_user).first()
        return [r.to_dict(rules=["-puppies"]) for r in parent]
    parents=PuppyAdult.query.filter_by(user=current_user).all()
    return [r.to_dict(rules=["-puppies",'-user']) for r in parents]

@app.route("/api/adults",methods=["POST"])
@login_required
def add_adults():
    data = request.form.to_dict()
    data['user_id'] = current_user.id

    try:
        adult = PuppyAdult(**data)
        db.session.add(adult)
        db.session.commit()
        return "success", 201
    except IntegrityError as e:
        db.session.rollback()
        return f"Error: {str(e)}", 400
    except Exception as e:
        db.session.rollback()
        return f"Unexpected Error: {str(e)}", 500

@app.route("/api/adults/<id>",methods=["DELETE"])
@login_required
def delete_adults(id):
    return "Done"

@app.route("/api/adults",methods=["PUT"])
@login_required
def update_adults():
    return "Done"


#######################
#Puppy CRUD-methodds #
#######################
@app.route("/api/puppies", methods=["GET"])
@login_required
def get_puppies():
    id = request.args.get("id")
    data = []

    if id:
        parent = PuppyAdult.query.filter_by(id=id, user_id=current_user.id).first()
        if parent and parent.puppies:
            for puppy in parent.puppies:
                puppy_dict = puppy.to_dict(rules=['-parent.puppies','-records','-recommendations', '-records', '-parent.user'])
                puppy_dict['age'] = calculate_puppy_age(puppy)
                data.append(puppy_dict)
    else:
        parents = PuppyAdult.query.filter_by(user_id=current_user.id).all()
        for parent in parents:
            if parent.puppies:
                for puppy in parent.puppies:
                    puppy_dict = puppy.to_dict(rules=['-parent.puppies','-records','-recommendations', '-records', '-parent.user'])
                    puppy_dict['age'] = calculate_puppy_age(puppy)
                    data.append(puppy_dict)

    return data

@app.route("/api/puppies",methods=["POST"])
@login_required
def add_puppies():
    data = request.form.to_dict()
    data["birth_date"] = datetime.datetime.strptime(
        data["birth_date"], "%Y-%m-%dT%H:%M")
    
    try:
        puppy = Puppy(**data)
        db.session.add(puppy)
        db.session.commit()
        return "Puppy added successfully!", 201
    except Exception as e:
        db.session.rollback()
        return f"Error: {str(e)}", 400

@app.route("/api/puppies",methods=["DELETE"])
@login_required
def delete_puppies():
    return "Done"



@app.route('/api/quick-check-puppy-health', methods=['POST'])
@login_required
def quick_check_puppy_health():
    data = request.form
   
    # weight = data.get("Weight")
    # day = data.get("Day")
    # temp = data.get("Temperature")
    # temp = data.get("")

    status,message=quick_check_recommendations_for_puppy(data)
    return {"status":status,"message":message}, 201

@app.route('/api/check-puppy-health', methods=['POST'])
@login_required
def check_puppy_health():
    data = request.form
    puppy_id = data.get("puppy_id")

    if not puppy_id:
        return "No Puppy has been provided", 404

    puppy = get_puppy_by_id(puppy_id, current_user.id)
    if not puppy:
        return "Puppy provided not found", 500
    
    weight = data.get("weight")
    _date = data.get("_date")
    temp = data.get("temperature")

    try:
        _date = datetime.datetime.strptime(_date, '%Y-%m-%d')  # Adjust date format as needed
    except ValueError:
        return "Invalid date format", 400
    
    return "Done", 201

@app.route('/api/update-puppy-health', methods=['POST'])
@login_required
def update_puppy_health():
    data = request.form
    puppy_id = data.get("puppy_id")

    if not puppy_id:
        return "No Puppy has been provided", 404

    puppy = get_puppy_by_id(puppy_id, current_user.id)
    if not puppy:
        return "Puppy provided not found", 500
    
    weight = data.get("weight")
    _date = data.get("_date")
    temp = data.get("temperature")

    try:
        _date = datetime.datetime.strptime(_date, '%Y-%m-%d')  # Adjust date format as needed
    except ValueError:
        return "Invalid date format", 400

    # Check if a record for the given date already exists
    existing_record = db.session.query(PuppyRecords).filter_by(puppy_id=puppy_id, date=_date).first()

    if existing_record:
        return "Record for this date already exists", 400

    # Create a new record
    record = PuppyRecords(date=_date, puppy_id=puppy_id, weight_value=weight, temp_value=temp)
    db.session.add(record)
    db.session.commit()
    update_recommendations_for_puppy(puppy)
    return "Done", 201


#######################
#Other APIs#
#######################
@app.route("/record_action", methods=["POST"])
@login_required
def record_action():
    user_id = current_user.id
    recommendation_id = request.form.get("recommendation_id")
    action_taken = request.form.get("action_taken")
    review_date = request.form.get("review_date")

    recommendation = Recommendation.query.get(recommendation_id)
    if action_taken == "Took puppy to vet" and recommendation:
        recommendation.follow_up_status = True
        if review_date:
            recommendation.follow_up_date = datetime.strptime(review_date, '%Y-%m-%d')
        db.session.commit()

    user_action = UserAction(
        user_id=user_id,
        recommendation_id=recommendation_id,
        action_taken=action_taken,
        review_date=review_date if review_date else None
    )
    db.session.add(user_action)
    db.session.commit()

    return redirect(url_for("recommendations"))




def _fk_pragma_on_connect(dbapi_con, con_record):
    dbapi_con.execute('pragma foreign_keys=ON')

with app.app_context():
    from sqlalchemy import event
    event.listen(db.get_engine(), 'connect', _fk_pragma_on_connect)
    db.create_all()
    
    build_sample_db(app,user_datastore)