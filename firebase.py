import pyrebase
import os
from dotenv import load_dotenv

firebaseConfig = {
    'apiKey': os.environ.get('FIREBASE_API_KEY'),
    'authDomain': os.environ.get('FIREBASE_AUTH_DOMAIN'),
    'databaseURL': os.environ.get('FIREBASE_DATABASE_URL'),
    'projectId': os.environ.get('FIREBASE_PROJECT_ID'),
    'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET'),
    'messagingSenderId': os.environ.get('FIREBASE_MESSAGING_SENDER_ID'),
    'appId': os.environ.get('FIREBASE_APP_ID'),
    'measurementId': os.environ.get('FIREBASE_MEASUREMENT_ID')
}

# Initialisation Firebase
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

def login(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return user
    except Exception as e:
        print("Login failed:", str(e))
        return None

def signup(email, password):
    try:
        user = auth.create_user_with_email_and_password(email, password)
        return user
    except Exception as e:
        print("Signup failed:", str(e))
        return None

def get_user_data(uid):
    try:
        data = db.child("users").child(uid).get().val()
        return data or {"expenses": [], "revenus": [], "budget": 0, "budget_expenses": []}
    except Exception as e:
        print("Error fetching user data:", str(e))
        return {"expenses": [], "revenus": [], "budget": 0, "budget_expenses": []}

def update_user_data(uid, data):
    try:
        db.child("users").child(uid).set(data)
    except Exception as e:
        print("Error updating user data:", str(e))