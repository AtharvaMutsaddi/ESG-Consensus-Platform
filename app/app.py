from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_moment import Moment
from flask_bcrypt import Bcrypt
import mysql.connector
import json
import pandas as pd
import nltk
import os
from werkzeug.utils import secure_filename
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

    # Extract the user's name from the email
    name = email.split("@")[0]
    # Get the organization ID (if it exists)
    organization_id = get_org_id(organization)
    if organization_id:
        organization_id = organization_id[0][0]
    else:
        organization_id = None  # Use None, not 'NULL'

    # Hash the user's password before saving it to the database
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    # Check if a profile picture file was uploaded
    if "profileImage" in request.files:
        profile_image = request.files["profileImage"]
        if profile_image.filename != "":
            # Save the profile picture to a folder and store the path in the database
            upload_folder = "static/profile_images"
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # Create a unique filename for the profile picture
            filename = os.path.join(upload_folder, secure_filename(profile_image.filename))
            profile_image.save(filename)

    # Use parameterized query to prevent SQL injection
    insert_query = "INSERT INTO User (Name, Email, Role, Password, OrganizationID, profile_pic) VALUES (%s, %s, %s, %s, %s, %s)"
    values = (name, email, role, hashed_password, organization_id, filename if "filename" in locals() else None)
    cursor.execute(insert_query, values)
    cnx.commit()

def fetch_comments_for_post(post_id):
    query = "SELECT Comment.CommentID, Comment.Content, Comment.CreatedAtDate, User.Name " \
            "FROM Comment " \
            "INNER JOIN User ON Comment.UserID = User.UserID " \
            "WHERE Comment.PostID = %s"
    cursor.execute(query, (post_id,))
    comments = []
    
    for comment_data in cursor.fetchall():
        comment = {
            'CommentID': comment_data[0],
            'Content': comment_data[1],
            'CreatedAtDate': comment_data[2],
            'Name': comment_data[3]
        }
        comments.append(comment)

    return comments

def create_new_post(form_data,user_id):
    title=form_data.get("title")
    description=form_data.get("description")
    topic=form_data.get("topic")
    type=form_data.get("type")
    upvotes=0
    downvotes=0
    query=f"SELECT OrganizationID from User where UserID={user_id}"
    cursor.execute(query)
    result=cursor.fetchall()
    OrganizationID=result[0][0]
    values = (title, description, topic,user_id, upvotes, downvotes,OrganizationID,type)
    insert_query = "INSERT INTO Post (Title, Description, Topic, UserID, Upvotes, Downvotes, OrganizationID, Type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(insert_query, values)
    cnx.commit()

def get_posts():
    query = f"SELECT Post.*,Name FROM Post join User using(UserID);"
    cursor.execute(query)
    result = cursor.fetchall()
    posts_df=pd.DataFrame(result,columns=["PostID","Title","Description","CreatedAtDate","Status","Topic","UserID","Upvotes","Downvotes","OrganizationID","Type","PostedBy"])
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

def fetch_post_from_database(post_id):
    query = "SELECT Post.PostID, Post.Title, Post.Description, Post.CreatedAtDate, Post.Topic, User.Name, Post.Upvotes, Post.Downvotes " \
            "FROM Post " \
            "INNER JOIN User ON Post.UserID = User.UserID " \
            "WHERE Post.PostID = %s"
    cursor.execute(query, (post_id,))
    post_data = cursor.fetchone()

    if post_data:
        post = {
            'PostID': post_data[0],
            'Title': post_data[1],
            'Description': post_data[2],
            'CreatedAtDate': post_data[3],
            'Topic': post_data[4],
            'Name': post_data[5],
            'Upvotes': post_data[6],
            'Downvotes': post_data[7]
        }

        return post

    return None

def insert_comment_into_database(comment_data, post_id):
    content = comment_data.get("content")
    user_id = session.get("user_id") 
    post_id = post_id

    insert_query = "INSERT INTO Comment (Content, UserID, PostId) VALUES (%s, %s, %s)"
    values = (content, user_id, post_id)
    cursor.execute(insert_query, values)
    cnx.commit()

def get_sentiment_analytics(post_id):
    q=f"SELECT * from Comment WHERE PostID={post_id};"
    cursor.execute(q)
    result=cursor.fetchall()
    comment_df=pd.DataFrame(result,columns=["CommentID","Content","CreatedAtDate","UserID","PostID"])
    comments=comment_df["Content"]
    sentiments=[]
    for comment in comments:
        sentiment_scores = sid.polarity_scores(comment)
        compound_score = sentiment_scores['compound']
        sentiments.append(compound_score)
    comment_df['CompoundScore'] = sentiments

    # Categorize comments as positive, negative, or neutral
    comment_df['SentimentLabel'] = 'neutral'
    comment_df.loc[comment_df['CompoundScore'] > 0.05, 'SentimentLabel'] = 'positive'
    comment_df.loc[comment_df['CompoundScore'] < -0.05, 'SentimentLabel'] = 'negative'
    return comment_df


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
    previous_route = session.get('previous_route', 'http://127.0.0.1:5000/home') 
    return redirect(previous_route)

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
    previous_route = session.get('previous_route', 'http://127.0.0.1:5000/home') 
    return redirect(previous_route)
@app.route("/home", methods=["GET", "POST"])
def home():
    posts_df=get_posts()
    session['previous_route'] = request.url
    checkloggedin=("user_id" in session)
    return render_template("home.html",posts_df=posts_df,checkloggedin=checkloggedin)

@app.route("/view_post/<int:post_id>", methods=["GET"])
def view_post(post_id):
    # Fetch the specific post from the database
    session['previous_route'] = request.url
    post = fetch_post_from_database(post_id)
    if post is None:
        flash("Post not found", "danger")
        return redirect(url_for("home"))

    # Fetch comments for the post
    comments = fetch_comments_for_post(post_id)
    df=get_sentiment_analytics(post_id)
    data = {
        'labels': list(df['SentimentLabel'].value_counts().index),
        'data': list(df['SentimentLabel'].value_counts().values),
        'colors': ['green', 'red', 'gray'],
    }
    data['data'] = [int(x) for x in data['data']]

    grouped = df.groupby(['CreatedAtDate', 'SentimentLabel']).size().unstack().fillna(0)

    # Check if 'positive', 'negative', and 'neutral' are present in the grouped DataFrame
    if 'positive' not in grouped:
        grouped['positive'] = [0] * len(grouped)
    if 'negative' not in grouped:
        grouped['negative'] = [0] * len(grouped)
    if 'neutral' not in grouped:
        grouped['neutral'] = [0] * len(grouped)

    data2 = {
        "labels": list(grouped.index),
        "positive": list(grouped['positive']),
        "negative": list(grouped['negative']),
        "neutral": list(grouped['neutral']),
    }

    data2['positive'] = [int(x) for x in data2['positive']]
    data2['negative'] = [int(x) for x in data2['negative']]
    data2['neutral'] = [int(x) for x in data2['neutral']]

    # Render a template to view the post with comments
    return render_template("view_post.html", post=post, comments=comments,data=data,data2=data2)

@app.route("/create_post", methods=["GET", "POST"])
def create_post():
    if request.method == "POST" and "user_id" in session:
        form_data = request.form.to_dict()
        user_id = session["user_id"]
        create_new_post(form_data,user_id)
        return redirect(url_for("home"))
    elif "user_id" not in session:
        flash("Please Login to add posts", "danger")
    return render_template("create_post.html")

@app.route("/logout", methods=["POST"])
def logout():
    if  request.method == "POST":
        session.clear()
        return redirect(url_for("signup"))

@app.route("/submit_comment/<int:post_id>", methods=["POST"])
def submit_comment(post_id):
    if request.method == "POST" and "user_id" in session:
        comment_data = request.form.to_dict()
        insert_comment_into_database(comment_data, post_id)  # Implement this function
        flash("Comment successfully added", "success")
        return redirect(url_for("view_post", post_id=post_id))
    elif "user_id" not in session:
        flash("Please Login to add comments", "danger")
    previous_route = session.get('previous_route', 'http://127.0.0.1:5000/home') 
    return redirect(previous_route)

@app.route("/my_post", methods=["GET", "POST"])
def my_posts():
    # Check if the user is logged in
    if "user_id" in session:
        user_id = session["user_id"]
        # Fetch posts created by the logged-in user
        query = f"SELECT * FROM Post WHERE UserID = {user_id}"
        cursor.execute(query)
        user_posts = cursor.fetchall()
        posts_df = pd.DataFrame(user_posts, columns=["PostID", "Title", "Description", "CreatedAtDate", "Status", "Topic","UserID", "Upvotes", "Downvotes", "OrganizationID", "Type"])
        post_id = 1
        checkloggedin = True
        return render_template("my_post.html", posts_df=posts_df, post_id = post_id, checkloggedin=checkloggedin)
    else:
        flash("Please log in to view your posts", "danger")
        return redirect(url_for("login"))

@app.route("/edit_post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    if "user_id" in session:
        if request.method == "POST":
            # Handle the form submission to update the post
            new_title = request.form.get("editTitle")
            new_description = request.form.get("editDescription")
            new_status = request.form.get("editStatus")
            new_topic = request.form.get("editTopic")
            new_type = request.form.get("editType")


            # Update the post in the database using a SQL query
            update_query = "UPDATE Post SET Title = %s, Description = %s, Status = %s, Topic = %s, Type = %s WHERE PostID = %s"
            cursor.execute(update_query, (new_title, new_description, new_status, new_topic, new_type, post_id))
            cnx.commit()

            flash("Post updated successfully", "success")
            return redirect(url_for("my_posts"))
        else:
            # Fetch the existing post data for pre-filling the form
            query = f"SELECT * FROM Post WHERE PostID = {post_id}"
            cursor.execute(query)
            post_data = cursor.fetchone()

            if post_data:
                post = {
                    'PostID': post_data[0],
                    'Title': post_data[1],
                    'Description': post_data[2],
                    'Status': post_data[4],
                    'Topic' : post_data[5],
                    'Type' : post_data[6]
                }
                return render_template("edit_post.html", post=post)
            else:
                flash("Post not found", "danger")
                return redirect(url_for("my_posts"))
    else:
        flash("Please log in to edit posts", "danger")
        return redirect(url_for("login"))

@app.route("/organization_info", methods=["GET","POST"])
def organization_info():
    # Check if the user is logged in
    if "user_id" in session:
        user_id = session["user_id"]
        checkloggedin = True
        query = f"SELECT * FROM Organization;"
        cursor.execute(query)
        other_organizations = cursor.fetchall()
        # Convert the list of dictionaries to a Pandas DataFrame
        other_organizations = pd.DataFrame(other_organizations, columns=["OrganizationID","Name","ContactInformation","Description","Location"])
        
        # other_organizations = fetch_other_organizations(user_id)

        return render_template("organization_info.html", other_organizations=other_organizations, checkloggedin=checkloggedin)
    else:
        flash("Please log in to view organization information", "danger")
        return redirect(url_for("login"))



@app.route("/delete_post/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    if "user_id" in session:
        user_id = session["user_id"]

        # Check if the post with the given ID exists and belongs to the logged-in user
        query = "SELECT UserID FROM Post WHERE PostID = %s"
        cursor.execute(query, (post_id,))
        result = cursor.fetchone()

        if result and result[0] == user_id:
            # If the post exists and belongs to the user, delete it
            delete_query = "DELETE FROM Post WHERE PostID = %s"
            cursor.execute(delete_query, (post_id,))
            cnx.commit()
            flash("Post deleted successfully", "success")
        else:
            flash("You don't have permission to delete this post", "danger")
    else:
        flash("Please log in to delete posts", "danger")

    # Redirect back to the "My Posts" page
    return redirect(url_for("my_posts"))

if __name__ == '__main__':
    app.run(debug=True)