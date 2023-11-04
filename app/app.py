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
def get_posts():
    query = f"SELECT Post.*,Name FROM Post join User using(UserID);"
    cursor.execute(query)
    result = cursor.fetchall()
    posts_df=pd.DataFrame(result,columns=["PostID","Title","Description","CreatedAtDate","Status","Topic","UserID","Upvotes","Downvotes","OrganizationID","PostedBy"])
    return posts_df
def has_user_upvoted(user_id, post_id):
    # Check if the user has upvoted the post
    query = f"SELECT VoteType FROM UserVotes WHERE UserID = {user_id} AND PostID = {post_id}"
    cursor.execute(query)
    result = cursor.fetchall()

    if len(result) > 0:
        votetype=result[0][0]
        if votetype=='downvote':
            # User has upvoted, handle downvoting logic
            # First, remove the previous upvote from the votes table
            delete_query = f"DELETE FROM UserVotes WHERE UserID = {user_id} AND PostID = {post_id};"
            cursor.execute(delete_query)
            cnx.commit()

            # Next, update the upvotes and downvotes in the posts table
            update_query = f"UPDATE Post SET Downvotes = Downvotes - 1 WHERE PostID = {post_id}"
            cursor.execute(update_query)
            cnx.commit()
            return False  # User has downvoted after the previous upvote
        else:
            return True
    else:
        return False  # User has not upvoted the post, they can upvote it
def insert_upvote(user_id, post_id):
    query = f"INSERT INTO UserVotes (UserID, PostID, VoteType) VALUES ({user_id}, {post_id}, 'upvote')"
    cursor.execute(query)
    cnx.commit()
    update_query = f"UPDATE Post SET Upvotes = Upvotes + 1 WHERE PostID = {post_id}"
    cursor.execute(update_query)
    cnx.commit()
def has_user_downvoted(user_id, post_id):
    query = f"SELECT VoteType FROM UserVotes WHERE UserID = {user_id} AND PostID = {post_id}"
    cursor.execute(query)
    result = cursor.fetchall()

    if len(result) > 0:
        votetype=result[0][0]
        if votetype=='upvote':
            delete_query = f"DELETE FROM UserVotes WHERE UserID = {user_id} AND PostID = {post_id};"
            cursor.execute(delete_query)
            cnx.commit()

            # Next, update the upvotes and downvotes in the posts table
            update_query = f"UPDATE Post SET Upvotes = Upvotes - 1 WHERE PostID = {post_id}"
            cursor.execute(update_query)
            cnx.commit()
            return False  
        else:
            return True
    else:
        return False 
def insert_downvote(user_id, post_id):
    query = f"INSERT INTO UserVotes (UserID, PostID, VoteType) VALUES ({user_id}, {post_id}, 'downvote')"
    cursor.execute(query)
    cnx.commit()
    update_query = f"UPDATE Post SET Downvotes = Downvotes + 1 WHERE PostID = {post_id}"
    cursor.execute(update_query)
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

@app.route("/upvote/<int:post_id>", methods=["POST"])
def upvote(post_id):
    # Check if the user is logged in
    if "user_id" in session:
        user_id = session["user_id"]
        # Check if the user has already upvoted the post
        if not has_user_upvoted(user_id, post_id):
            # Insert the upvote into the UserVotes table
            insert_upvote(user_id, post_id)
            flash("Upvoted successfully", "success")
        else:
            flash("You have already upvoted this post", "danger")
    else:
        flash("Please log in to upvote", "danger")

    # Redirect back to the post or home page
    return redirect(url_for("home")) 

@app.route("/downvote/<int:post_id>", methods=["POST"])
def downvote(post_id):
    # Check if the user is logged in
    if "user_id" in session:
        user_id = session["user_id"]
        # Check if the user has already upvoted the post
        if not has_user_downvoted(user_id, post_id):
            # Insert the upvote into the UserVotes table
            insert_downvote(user_id, post_id)
            flash("Downvoted successfully", "success")
        else:
            flash("You have already downvoted this post", "danger")
    else:
        flash("Please log in to downvote", "danger")

    # Redirect back to the post or home page
    return redirect(url_for("home"))
@app.route("/home", methods=["GET", "POST"])
def home():
    posts_df=get_posts()
    return render_template("home.html",posts_df=posts_df)

if __name__ == '__main__':
    app.run(debug=True)