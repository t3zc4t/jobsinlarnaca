import os
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from helpers import apology, login_required
import urllib.parse

import mysql.connector

project_folder = os.path.expanduser('~/mysite')  
load_dotenv(os.path.join(project_folder, '.env'))
SECRET_KEY = os.getenv("DB_PASS")

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    try:
        mydb = mysql.connector.connect(host = "jobsinlarnaca.mysql.pythonanywhere-services.com", user = "jobsinlarnaca", password = DB_PASS, database = "jobsinlarnaca$default")
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
    """Show all available Jobs"""
    mycursor = mydb.cursor(dictionary = True)
    mycursor.execute("SELECT DISTINCT users.companyname AS cname, jobs.userid, jobs.companyname, jobs.jobid, jobs.title, jobs.platform, jobs.dateposted, jobs.link FROM users INNER JOIN jobs ON users.userid = jobs.userid")
    resultlist = mycursor.fetchall()
    mycursor.close()
    mydb.close()
    return render_template("getjobs.html",resultlist=resultlist)

@app.route("/profile", methods = ["GET", "POST"])
@login_required
def private_profile():
    """Show Private Profile"""
    if request.method == "POST":
        #Update Database
        try:
            mydb = mysql.connector.connect(host = "jobsinlarnaca.mysql.pythonanywhere-services.com", user = "jobsinlarnaca", password = "DB_PASS", database = "jobsinlarnaca$default")
        except mysql.connector.Error as err:
            print("Something went wrong: {}".format(err))
        cursor = mydb.cursor()
        try:
            cursor.execute("UPDATE users SET companyname = %s, address = %s, websitelink = %s WHERE userid = %s", (request.form.get("cname"), request.form.get("address"), request.form.get("websitelink"), session["user_id"]))
            mydb.commit()
            sql_select = "SELECT * FROM users WHERE userid = %s"
            cursor.execute(sql_select, (session["user_id"], ))
            row = cursor.fetchone()
            flash("Profile updated")
        except mysql.connector.Error as err:
            print("MySQL Error %s",err)
            return apology("Database Error", 400)
        finally:
            cursor.close()
            mydb.close()
            return render_template("private_profile.html",row = row)

    else:
        sql_select = "SELECT * FROM users WHERE userid = %s"
        # Check if username already exists
        try:
            mydb = mysql.connector.connect(host = "jobsinlarnaca.mysql.pythonanywhere-services.com", user = "jobsinlarnaca", password = "DB_PASS", database = "jobsinlarnaca$default")
        except mysql.connector.Error as err:
            print("Something went wrong: {}".format(err))
        cursor = mydb.cursor()
        cursor.execute(sql_select, (session["user_id"],))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            mydb.close()
            return apology("company doesn't exist", 400)
        else:
            mycursor = mydb.cursor(dictionary=True)
            mycursor.execute("SELECT * FROM jobs WHERE userid = %s", (session["user_id"], ))
            resultlist = mycursor.fetchall()
            cursor.close()
            mycursor.close()
            mydb.close()
            return render_template("private_profile.html", row = row, resultlist = resultlist)


@app.route("/removejob/<jobid>")
@login_required
def removejob(jobid):
    """Remove Job"""
    try:
            mydb = mysql.connector.connect(host = "jobsinlarnaca.mysql.pythonanywhere-services.com", user = "jobsinlarnaca", password = "DB_PASS", database = "jobsinlarnaca$default")
    except mysql.connector.Error as err:
            print("Something went wrong: {}".format(err))
    cursor = mydb.cursor()
    try:
        cursor.execute("DELETE FROM jobs WHERE userid = %s AND jobid = %s", (session["user_id"], jobid))
        mydb.commit()
        flash("Listing removed")
    except mysql.connector.Error as err:
        print("MySQL Error %s", err)
        return apology("Database Error", 400)
    finally:
        cursor.close()
        mydb.close()
    return redirect("/profile")

@app.route("/postjob", methods = ["GET", "POST"])
@login_required
def postjob():
    """Post new Job"""
    if request.method == "POST":
        try:
            mydb = mysql.connector.connect(host = "jobsinlarnaca.mysql.pythonanywhere-services.com", user = "jobsinlarnaca", password = "DB_PASS", database = "jobsinlarnaca$default")
        except mysql.connector.Error as err:
            print("Something went wrong: {}".format(err))
        currdate = datetime.utcnow().strftime("%Y-%m-%d")
        cursor = mydb.cursor()
        try:
            cursor.execute("INSERT INTO jobs (userid, title, longdescription, dateposted, platform) VALUES (%s, %s, %s, %s, %s)", (session["user_id"], request.form.get("title"), request.form.get("description"),currdate, "JIL"))
            mydb.commit()
            flash("Job published")
        except mysql.connector.Error as err:
            print("MySQL Error %s", err)
            return apology("Database Error", 400)
        finally:
            cursor.close()
            mydb.close()
            return redirect("/profile")
    else:
        return render_template("postjob.html")


@app.route("/companies/<cname>")
def public_profile(cname):
    """Show Public Profile"""
    companyname = urllib.parse.unquote(cname)
    sql_select = "SELECT * FROM users WHERE companyname = %s"
    # Check if username already exists
    try:
        mydb = mysql.connector.connect(host = "jobsinlarnaca.mysql.pythonanywhere-services.com", user = "jobsinlarnaca", password = "DB_PASS", database = "jobsinlarnaca$default")
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
    cursor = mydb.cursor()
    cursor.execute(sql_select, (companyname, ))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        mydb.close()
        return apology("company doesn't exist", 400)
    else:
        mycursor = mydb.cursor(dictionary = True)
        mycursor.execute("SELECT users.companyname, jobs.userid, jobs.jobid, jobs.title, jobs.dateposted, jobs.longdescription FROM users INNER JOIN jobs ON users.userid = jobs.userid WHERE users.companyname = %s",(companyname,))
        resultlist = mycursor.fetchall()
        mycursor.close()
        cursor.close()
        mydb.close()
        return render_template("public_profile.html", row = row, resultlist = resultlist)



@app.route("/job-listings/<jobid>")
def internal_job_listing(jobid):
    """Show Internal Job Listing Page"""
    sql_select = "SELECT users.companyname, users.userid, jobs.userid FROM users INNER JOIN jobs ON users.userid = jobs.userid WHERE jobs.jobid = %s"
    try:
        mydb = mysql.connector.connect(host = "jobsinlarnaca.mysql.pythonanywhere-services.com", user = "jobsinlarnaca", password = "DB_PASS", database = "jobsinlarnaca$default")
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
    cursor = mydb.cursor(dictionary = True)
    cursor.execute(sql_select, (jobid, ))
    row = cursor.fetchone()
    cname = row['companyname']
    sql_select = "SELECT * FROM jobs WHERE jobid=%s"
    cursor = mydb.cursor(dictionary = True)
    cursor.execute(sql_select, (jobid,))
    resultlist = cursor.fetchone()
    cursor.close()
    mydb.close()
    if not resultlist:
        return apology("jobid doesn't exist", 400)
    return render_template("job.html",resultlist = resultlist,cname = cname)


@app.route("/login", methods = ["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        try:
            mydb = mysql.connector.connect(host = "jobsinlarnaca.mysql.pythonanywhere-services.com", user = "jobsinlarnaca", password = "DB_PASS", database = "jobsinlarnaca$default")
        except mysql.connector.Error as err:
            print("Something went wrong: {}".format(err))
        db = mydb.cursor(dictionary=True)
        db.execute("SELECT * FROM users WHERE username = %s", (request.form.get("username"), ))
        row = db.fetchone()

        # Ensure username exists and password is correct
        if not row or not check_password_hash(row["password"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = row["userid"]
        db.close();
        mydb.close()
        # Redirect user to home page
        flash("Logged in successfully")
        return redirect("/profile")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods = ["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        sql_select = "SELECT * FROM users WHERE username = %s"

        # Check if username already exists
        try:
            mydb = mysql.connector.connect(host = "jobsinlarnaca.mysql.pythonanywhere-services.com", user = "jobsinlarnaca", password = "DB_PASS", database = "jobsinlarnaca$default")
        except mysql.connector.Error as err:
            print("Something went wrong: {}".format(err))
        cursor = mydb.cursor()
        cursor.execute(sql_select, (request.form.get("username"), ))
        row = cursor.fetchone()
        if row:
            cursor.close()
            mydb.close()
            return apology("username already exists", 400)

        #Apology if either input is blank or the passwords do not match
        if not request.form.get("password") or not request.form.get("confirmation") or request.form.get("confirmation") != request.form.get("password"):
            cursor.close()
            mydb.close()
            return apology("please setup a password and make sure you confirm it", 400)

        email=request.form.get("email")
        if not email:
            email = ""

        # Insert user into database
        currdate = datetime.utcnow().strftime("%Y-%m-%d")
        try:
            cursor.execute("INSERT INTO users (username, password, createdtime,email) VALUES (%s,%s,%s,%s)", (request.form.get("username"), generate_password_hash(request.form.get("password")), currdate, email))
            mydb.commit()
            cursor.execute("SELECT * FROM users WHERE username = %s", (request.form.get("username"),))
            row = cursor.fetchone()

            # Remember which user has logged in
            session["user_id"] = row[0]
        except mysql.connector.Error as err:
            print("MySQL Error %s", err)
            return apology("Database Error", 400)
        finally:
            cursor.close()
            mydb.close()
            flash("Profile created successfully")
            # Redirect user to home page"""
            return redirect("/")

    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash("Logged out successfully")
    return redirect("/")

if __name__ == "__main__":
app.run(debug=True)

