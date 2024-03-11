from flask import Flask
from flask import request, render_template
import pandas as pd
import numpy as np
import pickle
app = Flask(__name__,
            static_url_path='',
            static_folder='static',

            template_folder='templates')

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
def hello():
    return render_template('index.html',
                           page="index")

@app.route("/puppies/<id>")
def get_puppy_details(id):
    return render_template("view_puppy.html")

@app.route("/<page>")
def pages(page):
    return render_template(page+'.html',
                           page=page)


if __name__ == "__main__":
    app.run(debug=True)
