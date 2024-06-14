# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, DateField
from wtforms.validators import DataRequired, Length, NumberRange

class PuppyForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=50)])
    breed = StringField('Breed', validators=[DataRequired(), Length(max=50)])
    birth_date = DateField('Birth Date', format='%Y-%m-%d', validators=[DataRequired()])
    weight = FloatField('Weight (kg)', validators=[DataRequired(), NumberRange(min=0)])
    temperature = FloatField('Temperature (°C)', validators=[DataRequired(), NumberRange(min=25, max=42)])
