import os

#library for CS50 that includes fucntionality for writing SQL in Python
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required
from datetime import date
import datetime
import calendar

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (local, instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///users.db")

#function for checking whether two dates are consecutive
def consec(date_1, date_2):
    day_1 = int(date_1[8:10])
    day_2 = int(date_2[8:10])
    month_1 = int(date_1[5:7])
    month_2 = int(date_2[5:7])
    if (day_1 - 1) == day_2 and month_1 == month_2:
        return 1
    else:
        return 0

#overview (stats) route
@app.route("/overview", methods=["GET", "POST"])
@login_required
def overview():
    #if user is looking for a specific entry by date
    if request.method == "POST":
        date_submit = request.form.get("date")
        lookups = db.execute("SELECT timestamp, mood, anxiety, enjoyment, satisfaction, entry FROM entries WHERE user_id = ? AND timestamp = ?", session["user_id"], date_submit)
        for lookup in lookups:
            timestamp = lookup["timestamp"]
            mood = str(lookup["mood"])
            anxiety = str(lookup["anxiety"])
            enjoyment = str(lookup["enjoyment"])
            satisfaction = str(lookup["satisfaction"])
            entry = str(lookup["entry"])

        #returns a new page with the requested entry
        return render_template("past.html", lookups=lookups)
    else:
        #display stats
        extract = db.execute("SELECT username FROM users WHERE id = :id", id = session["user_id"])
        name = extract[0]['username'] #variable for name

        #determine number of entries
        entries = db.execute("SELECT COUNT(*) AS count FROM entries WHERE user_id = :id", id = session["user_id"])
        count = entries[0]['count']
        five = 1
        if count < 5:
            #if award is present
            five = 0

        #determine if person has written for the past 5 days
        dates = db.execute("SELECT timestamp FROM entries WHERE user_id = :id ORDER BY timestamp DESC", id = session["user_id"])
        counter = 0
        gap = 0
        est = timezone('EST')
        today = str(date.today())
        last = str(dates[0]['timestamp'])

        #if the person has written today
        length = len(dates) - 1
        if last == today:
            for i in range(length):
                if gap == 1:
                    continue
                else:
                    date_1 = str(dates[i]['timestamp'])
                    date_2 = str(dates[i+1]['timestamp'])
                    con = consec(date_1, date_2)
                    if con == 1:
                        counter = counter + 1
                    else:
                        gap = 1
        counter = counter + 1
        streak = 1
        if counter < 5:
            streak = 0

        #get averages for mood, anxiety, enjoyment, satisfaction (count = # entries)
        mood = db.execute("SELECT mood, anxiety, enjoyment, satisfaction FROM entries WHERE user_id = :id", id = session["user_id"])
        happy = 0
        neutral = 0
        sad = 0
        n_a_p = 0
        n_a = 0
        s_a_p=0
        s_a=0
        v_a_p=0
        v_a=0
        yes =0
        no=0
        very=0
        some=0
        not_s=0
        for i in range(count):
            if mood[i]["mood"] == 'Happy':
                happy = happy+1
            if mood[i]["mood"] == 'Neutral':
                neutral = neutral+1
            if mood[i]["mood"] == 'Sad':
                sad = sad+1
            if mood[i]["anxiety"] == 'Not at all':
                n_a = n_a+1
            if mood[i]["anxiety"] == 'Somewhat':
                s_a = s_a+1
            if mood[i]["anxiety"] == 'Very':
                v_a = v_a+1
            if mood[i]["enjoyment"] == 'Yes':
                yes = yes +1
            if mood[i]["enjoyment"] == 'No':
                no = no + 1
            if mood[i]["satisfaction"] == 'Very':
                very = very + 1
            if mood[i]["satisfaction"] == 'Somewhat':
                some = some + 1
            if mood[i]["satisfaction"] == 'Not satisfied':
                not_s=not_s + 1

        happy_percent = round(float(happy / count) * 100)
        neutral_percent = round(float(neutral / count) * 100)
        sad_percent = round(float(sad / count) * 100)
        n_a_p = round(float(n_a / count) * 100)
        s_a_p = round(float(s_a / count) * 100)
        v_a_p = round(float(v_a / count) * 100)
        y_p = round(float(yes / count) * 100)
        n_p = round(float(no / count) * 100)
        very_p = round(float(very / count) * 100)
        some_p = round(float(some / count) * 100)
        not_p = round(float(not_s / count) * 100)

        days = db.execute("SELECT timestamp FROM entries WHERE user_id = :id ORDER BY timestamp DESC", id = session["user_id"])

        for day in days:
            timestamp = str(day["timestamp"])

        return render_template("overview.html", days=days, today=today, dates=dates, very=very, some=some, not_s=not_s, very_p=very_p, some_p=some_p, not_p=not_p, yes=yes, no=no, y_p=y_p, n_p=n_p, n_a=n_a, n_a_p=n_a_p, s_a=s_a, s_a_p=s_a_p, v_a=v_a, v_a_p=v_a_p, count=count, counter=counter, five=five, streak=streak, happy_percent=happy_percent, happy=happy, sad=sad, neutral=neutral, sad_percent=sad_percent, neutral_percent=neutral_percent)

#route for submitting a new entry into your smart journal
@app.route("/entry", methods=["GET", "POST"])
@login_required
def entry():
    if request.method == "POST":
        mood = request.form.get("mood")
        anxiety = request.form.get("anxiety")
        enjoyment = request.form.get("enjoyment")
        satisfaction = request.form.get("satisfaction")
        entry = request.form.get("entry")
        my_date = date.today()
        day = calendar.day_name[my_date.weekday()]

        #inserts new entry into SQL database
        db.execute("INSERT INTO entries (user_id, mood, anxiety, enjoyment, satisfaction, entry, day) VALUES (?, ?, ?, ?, ?, ?, ?)", session["user_id"], mood, anxiety, enjoyment, satisfaction, entry, day)
        return redirect("/")

    else:
        return render_template("entry.html")

#homepage route when logged-in
@app.route("/")
@login_required
def index():
    """This is where someone will see right when they log in (show either see overview or new entry) """

    extract = db.execute("SELECT username FROM users WHERE id = :id", id = session["user_id"])
    name = extract[0]['username']


    return render_template("home.html", name = name)

#log-in route
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":                #if the user was actually trying to submit some data (fill out the log in form)

        # Ensure username was submitted (check for error conditions)
        if not request.form.get("username"):                    #request.form is the name of the form the user submitted and if we try to get the form with the title 'username' and there's nothing there, then we're going to return an apology
            message = "you must enter a username"
            return render_template("apology.html", message = message)

        # Ensure password was submitted
        elif not request.form.get("password"):                  #same as above, but with password field
            message = "you must enter a password"
            return render_template("apology.html", message = message)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",                #the : denotes a placeholder, will get back a list of all matching rows to this query
                          username=request.form.get("username"))                           # this line sets username equal to the value typed into the username field by the user

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):    #if less than 1 row or more than 1 row is returned, the username doesn't exist, if the pw doesn't matched the pw hash value in the database, the pw is wrong
            message = "invalid username and/or password"
            return render_template("apology.html", message = message)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]                          #creates a variable to remember the id of the returned row from the usernmae query

        # Redirect user to home page
        return redirect("/")                                        #redirects them back to / (the index route)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

#logout route
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

#register route (make a new account)
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        # Ensure username was submitted (check for error conditions)
        if not request.form.get("username"):                    #request.form is the name of the form the user submitted and if we try to get the form with the title 'username' and there's nothing there, then we're going to return an apology
            message = "you must enter a username"
            return render_template("apology.html", message = message)

        # Ensure password was submitted
        elif not request.form.get("password"):                  #same as above, but with password field
            message = "you must enter a password"
            return render_template("apology.html", message = message)

        # Ensure password was confirmed
        elif request.form.get("password") != request.form.get("confirmation"):                  #same as above, makes sure passwords match
            message = "these passwords do not match"
            return render_template("apology.html", message = message)
        else:
            hashed_pw = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)      #make hashed pw
            rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
            if len(rows) != 0:
                message = "this username is already taken"
                return render_template("apology.html", message = message)
            else:
                db.execute ("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), hashed_pw)
                return render_template("login.html")

    else:                                           #if no action taken, just return the html file with the register form
        return render_template("register.html")