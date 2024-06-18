import unittest
from flask_testing import TestCase
# Assume the function is defined in a module named `puppy_health`
from app.utils import determine_puppy_health_from_temperature

class TestPuppyHealth(TestCase):
    def create_app(self):
        # Flask app is required for Flask-Testing, but we won't use it in this case
        from flask import Flask
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app

    def test_normal_temperature_1_2_weeks(self):
        status, message = determine_puppy_health_from_temperature(1, 36.8)
        self.assertEqual(status, "NORMAL")
        self.assertEqual(message, "A temperature of 36.8 degrees Celsius is within the normal expected temperature range.")

    def test_normal_temperature_2_4_weeks(self):
        status, message = determine_puppy_health_from_temperature(3, 37.0)
        self.assertEqual(status, "NORMAL")
        self.assertEqual(message, "A temperature of 37.0 degrees Celsius is within the normal expected temperature range.")

    def test_slightly_high_temperature(self):
        status, message = determine_puppy_health_from_temperature(2, 38.0)
        self.assertEqual(status, "SLIGHTLY_HIGH")
        self.assertEqual(message, "Puppy temperature is slightly higher than normal, monitor your puppy closely for any signs of discomfort or unusual behavior.")

    def test_mild_fever_temperature(self):
        status, message = determine_puppy_health_from_temperature(3, 39.5)
        self.assertEqual(status, "MILD_FEVER")
        self.assertEqual(message, "Temperature indicates signs of mild fever. Monitor closely for any signs of discomfort or unusual behavior. Ensure hydration and comfort. If symptoms persist or worsen, consult a veterinarian.")

    def test_moderate_fever_temperature(self):
        status, message = determine_puppy_health_from_temperature(2, 40.0)
        self.assertEqual(status, "MODERATE_FEVER")
        self.assertEqual(message, "Temperature indicates a significant elevation in body temperature. Monitor closely for any signs of discomfort or unusual behavior. Ensure hydration and comfort. Consider consulting a veterinarian for further evaluation and guidance.")

    def test_high_fever_temperature(self):
        status, message = determine_puppy_health_from_temperature(3, 41.0)
        self.assertEqual(status, "HIGH_FEVER")
        self.assertEqual(message, "Urgent!!! Please consult a veterinarian urgently for assessment and appropriate treatment.")

    def test_slightly_lower_temperature(self):
        status, message = determine_puppy_health_from_temperature(1, 34.5)
        self.assertEqual(status, "SLIGHTLY_LOWER")
        self.assertEqual(message, "Puppy temperature is slightly lower than normal, monitor your puppy closely for any signs of discomfort or unusual behavior.")

    def test_hypothermia_temperature(self):
        status, message = determine_puppy_health_from_temperature(2, 33.0)
        self.assertEqual(status, "HYPOTHERMIA")
        self.assertEqual(message, "Your puppy's temperature is below normal range indicating potential hypothermia. Ensure your puppy is kept warm and comfortable immediately. Wrap your puppy in a blanket and provide a warm environment. Seek veterinary attention promptly for further evaluation and treatment to prevent further complications.")

    def test_invalid_age(self):
        status, message = determine_puppy_health_from_temperature(5, 36.8)
        self.assertEqual(status, "Invalid age range. Please provide an age between 1-4 weeks.")
        self.assertEqual(message, None)

if __name__ == '__main__':
    unittest.main()
