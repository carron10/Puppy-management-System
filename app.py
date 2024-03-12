from flask import Flask
from flask import request, render_template
import pandas as pd
import numpy as np
import pickle
import os
import json
import time
import psycopg2
from flask import (
    Flask,
    url_for,
    redirect,
    render_template,
    request,
    jsonify,
    send_from_directory,
)
from flask_security.utils import hash_password
from sqlalchemy import select, update
from flask_security import (
    Security,
    SQLAlchemyUserDatastore,
    current_user,
    login_required,
)
from flask_security.forms import RegisterForm
from flask_security.forms import StringField
from flask_security.forms import Required
from models import (db,User,Role)
from flask import Blueprint, request, Response, current_app

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

@app.route('/predict',methods=['POST'])
def getdata():
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

@app.route("/")
@app.route("/index.html")
@login_required
def hello():
    return render_template('index.html',
                           page="index")

@app.route("/puppies/<id>")
@login_required
def get_puppy_details(id):
    return render_template("view_puppy.html")

@app.route("/<page>")
@login_required
def pages(page):
    return render_template(page+'.html',
                           page=page)


with app.app_context():
    db.create_all()