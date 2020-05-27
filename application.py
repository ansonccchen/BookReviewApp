import os
import csv
import hashlib
import requests

from flask import Flask, session, render_template, redirect, jsonify, flash
from flask import request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from passlib.hash import sha256_crypt, pbkdf2_sha256

from helpers import *


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET","POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # check if username was submitted
        if not username:
            return render_template("login.html", noUser = True, noPass = False, invalid = False)
        # check if password was submitted
        if not password:
            return render_template("login.html", noUser = False, noPass = True, invalid = False)
        # check if username exists and valid username & password
        usernameExists = db.execute("SELECT * FROM users WHERE username = :username",
                            {"username": username}).fetchone()
        if usernameExists and pbkdf2_sha256.verify(password, usernameExists[2]):
            session["user_id"] = usernameExists[0]
            session["username"] = usernameExists[1]
            return redirect("/home")
        return render_template("login.html", noUser = False, noPass = False, invalid = True)
    return render_template("login.html", noUser = False, noPass = False, invalid = False)

@app.route("/register", methods=["GET","POST"])
def register():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # check if username was submitted
        if not username:
            return render_template("register.html", noUser = True, userTaken = False, noPass = False)
        # check if username already exists
        usernameTaken = db.execute("SELECT * FROM users WHERE username = :username",
                            {"username":username}).fetchone()
        if usernameTaken:
            return render_template("register.html", noUser = False, userTaken = True, noPass = False)
        # check if password was submitted
        if not password:
            return render_template("register.html", noUser = False, userTaken = False, noPass = True)
        # insert login and password into database
        hashPass = pbkdf2_sha256.hash(password)
        db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
            {"username": username, "password": hashPass})
        db.commit()
        flash("Successful registration, you can now log in")
        return redirect("/login")
    return render_template("register.html", noUser = False, userTaken = False, noPass = False)


@app.route("/home", methods=["GET","POST"])
@login_required
def home():
    if request.method == "POST":
        text = request.form.get("text")
        data = db.execute("SELECT * FROM books WHERE title iLIKE '%"+text+"%' OR author iLIKE '%"+text+"%' OR isbn iLIKE '%"+text+"%'").fetchall()
        return render_template("home.html", data = data, show = True)
    return render_template("home.html", show = False)

@app.route("/books/<string:isbn>", methods=["GET","POST"])
@login_required
def books(isbn):
    show = False
    if request.method == "POST":
        current = session["username"]
        rating = int(request.form.get("rating"))
        review = request.form.get("text-review")
        dupe_review = db.execute("SELECT * FROM reviews WHERE isbn = :isbn AND username = :username",
                        {"isbn": isbn, "username": current}).fetchone()
        if not dupe_review == None:
            show = True
        else:
            db.execute("INSERT INTO reviews (isbn, rating, text, username) VALUES (:isbn, :rating, :text, :username)",
                {"isbn": isbn, "rating": rating, "text": review, "username": current})
            db.commit()
            return redirect("/books/"+isbn)
    books = db.execute("SELECT * FROM books WHERE isbn = :isbn", 
                {"isbn": isbn}).fetchone()
    data = db.execute("SELECT * FROM reviews WHERE isbn = :isbn",
                {"isbn": isbn}).fetchall()
    # replace key with own goodreads key to run
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "eZE2J811Y5r9FUDlsgB5Ag", "isbns": isbn})
    average_rating=res.json()['books'][0]['average_rating']
    num_ratings=res.json()['books'][0]['work_ratings_count']
    book_info = []
    book_info.append(average_rating)
    book_info.append(num_ratings)
    return render_template("books.html", book=books, data=data, book_info=book_info, show=show)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")