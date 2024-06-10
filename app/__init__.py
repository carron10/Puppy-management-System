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
from app.models import Role, User, db,Puppy,PuppyAdult,build_sample_db,PuppyRecords
from app.utils import get_puppies_for_user,get_puppy_by_id,calculate_puppy_age
app = Flask(__name__,static_url_path='', static_folder='static', template_folder='templates')
app.config.from_pyfile('config.py')
db.init_app(app)


# Security
user_datastore = SQLAlchemyUserDatastore(db, User,Role)

# extend fields for registration form
class ExtendedRegisterForm(RegisterForm):
    first_name = StringField("First Name", [Required()])
    last_name = StringField("Last Name", [Required()])

# security
security = Security(app, user_datastore, register_form=ExtendedRegisterForm)

categories={0:"Good",1:"Monitor",2:"Vetinary"}




@app.route("/")
@app.route("/index.html")
@login_required
def hello():
    data={}
    data['puppies']=get_puppies()
    return render_template('index.html',
                           page="index",**data)

@app.route("/puppies/<id>")
@login_required
def get_puppy_details(id):
    data={}
    puppy=Puppy.query.filter_by(id=id).first()
    if not puppy:
        puppy=Puppy()
    data['puppy']=puppy
    return render_template("view_puppy.html",**data)

@app.route("/puppies")
@login_required
def puppies_page():
    data={}
    data['puppies']=get_puppies()
    data['adults']=get_adults()
    return render_template('puppies.html',**data,page="puppies")

@app.route("/adults")
@login_required
def adults():
    data={} 
    data['adults']=get_adults()
    return render_template('adults.html',page="adults",**data)

@app.route("/adults/<id>")
@login_required
def view_adult_details(id):
    data={}
    puppy_adult=PuppyAdult.query.filter_by(id=id).first()
    if not puppy_adult:
        puppy_adult=PuppyAdult()
    data['puppy_adult']=puppy_adult
    data['puppies']=puppy_adult.puppies
    return render_template("view_adult.html",**data)

@app.route("/recommendations")
@login_required
def recommendations():
    return render_template('recommendations.html',page="recommendations")




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
        return f"Error: {str(e.orig)}", 400
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
                puppy_dict = puppy.to_dict(rules=['-parent.puppies', '-records', '-parent.user'])
                puppy_dict['age'] = calculate_puppy_age(puppy)
                data.append(puppy_dict)
    else:
        parents = PuppyAdult.query.filter_by(user_id=current_user.id).all()
        for parent in parents:
            if parent.puppies:
                for puppy in parent.puppies:
                    puppy_dict = puppy.to_dict(rules=['-parent.puppies', '-records', '-parent.user'])
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
        return f"Error: {str(e.orig)}", 400

@app.route("/api/puppies",methods=["DELETE"])
@login_required
def delete_puppies():
    return "Done"

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
    record = PuppyRecords(date=_date, puppy_id=puppy_id, weigth_value=weight, temp_value=temp)
    db.session.add(record)
    db.session.commit()
    
    return "Done", 201


#######################
#Other APIs#
#######################

@app.route('/predict',methods=['POST'])
def predict_():
    data_to_predict = dict(request.get_json())
    data_to_predict=pd.DataFrame(data_to_predict)
    data_to_predict=np.array(data_to_predict)
    # Load the saved model
    with open('puppy_management_system_random_forest_model.pkl', 'rb') as file:
        loaded_rf_classifier = pickle.load(file)
# Load the saved model
    with open('puppy_management_system_decision_tree_model.pkl', 'rb') as file:
        loaded_dct_classifier = pickle.load(file)

    dct_y_pred = loaded_dct_classifier.predict(data_to_predict)
    rf_y_pred = loaded_rf_classifier.predict(data_to_predict)
    results_1=categories[dct_y_pred[0]]
    results_2=categories[rf_y_pred[0]]
    return f"Puppy Status: RF: {results_2} DCT:{results_1}"


def _fk_pragma_on_connect(dbapi_con, con_record):
    dbapi_con.execute('pragma foreign_keys=ON')

with app.app_context():
    from sqlalchemy import event
    event.listen(db.get_engine(), 'connect', _fk_pragma_on_connect)
    db.create_all()
    
    # build_sample_db(app,user_datastore)