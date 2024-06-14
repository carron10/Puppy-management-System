from flask import Blueprint, render_template, redirect, url_for
from .forms import PuppyForm

puppy_bp = Blueprint('puppy', __name__)

@puppy_bp.route('/learn', methods=['GET', 'POST'])
def add_puppy():
    form = PuppyForm()
    if form.validate_on_submit():
        # Save the new puppy to the database or perform any other necessary actions
        # For demonstration purposes, let's just print the puppy details
        print("New Puppy Details:")
        print("Name:", form.name.data)
        print("Breed:", form.breed.data)
        print("Birth Date:", form.birth_date.data)
        print("Weight:", form.weight.data)
        print("Temperature:", form.temperature.data)
        
        return redirect(url_for('index'))  # Redirect to homepage after adding puppy

    return render_template('learn.html', form=form)
