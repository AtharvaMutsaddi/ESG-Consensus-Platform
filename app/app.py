from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_moment import Moment
from flask_bcrypt import Bcrypt
import mysql.connector
import json
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
sid = SentimentIntensityAnalyzer()
with open("config.json", "r") as f:
    config = json.load(f)
# Create a database connection
cnx = mysql.connector.connect(
    host="localhost",  # Update with your host
    user=config["username"],
    password=config["password"],
    database="project"
)
# Create a cursor object to execute SQL queries
cursor = cnx.cursor()
app = Flask(__name__)
bcrypt = Bcrypt(app)
moment = Moment(app)
app.secret_key = '1234567890'
def get_user_by_email(email):
    query = f"SELECT * FROM User WHERE Email = '{email}'"
    cursor.execute(query)
    result = cursor.fetchall()
    return result
def get_org_id(name):
    query=f"SELECT OrganizationID FROM Organization where Name='{name}'"
    cursor.execute(query)
    result = cursor.fetchall()
    return result
def create_new_user(form_data):
    email = form_data.get("email")
    password = form_data.get("password")
    role = form_data.get("role")  # Assuming "role" is the name of the checkbox
    organization = form_data.get("organization")
    # Hash the user's password before saving it to the database
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    # Extract the user's name from the email
    name = email.split("@")[0]
    # Get the organization ID (if it exists)
    organization_id = get_org_id(organization)
    if organization_id:
        organization_id = organization_id[0][0]
    else:
        organization_id = None  # Use None, not 'NULL'
    # Use parameterized query to prevent SQL injection
    insert_query = "INSERT INTO User (Name, Email, Role, Password, OrganizationID) VALUES (%s, %s, %s, %s, %s)"
    values = (name, email, role, hashed_password, organization_id)
    cursor.execute(insert_query, values)
    cnx.commit()
    
# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Fetch user from the database based on the provided email
        user = get_user_by_email(email)  # Replace with your database logic

        if len(user)>0:
            user=user[0]
            # Check if the provided password matches the hashed password in the database
            if bcrypt.check_password_hash(user[4], password):
                # Set a session variable to track the user's session
                session["user_id"] = user[0]
                flash("Login successful", "success")
                return redirect(url_for("home"))  # Redirect to the home page upon successful login
            else:
                flash("User with the entered Credentials was not found. Please try again.", "danger")
        else:
            flash("User with the entered Credentials was not found. Please try again.", "danger")

    return render_template("login.html")  # Display the login form
# Signup route
@app.route("/", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # Capture all form inputs as a dictionary
        form_data = request.form.to_dict()
        email = form_data.get("email")
        if len(get_user_by_email(email)) > 0:
            flash("A user with this Email already exists", "danger")
        else:
            create_new_user(form_data)
            flash("Signup successful", "success")
            return redirect(url_for("home"))  # Redirect to the home page upon successful signup
    return render_template("signup.html")  # Display the signup form

@app.route("/home", methods=["GET", "POST"])
def home():
    return render_template("home.html")

if __name__ == '__main__':
    app.run(debug=True)