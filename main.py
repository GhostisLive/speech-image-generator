from flask import Flask, jsonify
from flask import render_template, redirect, request, session
from flask_session import Session
import openai
from openai.error import InvalidRequestError
from src.helpers import session_data, ses_keys, mysql_creds, validate_email
from src.database import create_tables
import src.colours as colours
from src.smtp import create_smtp_conn, send_email
import string
import random
import pymysql.cursors
from smtplib import SMTPRecipientsRefused
import os

#Connect to database and initialize
conn = pymysql.connect(**mysql_creds(), autocommit=True, cursorclass=pymysql.cursors.DictCursor)
create_tables(conn)

#Initialize openai
openai.api_key = os.environ["OPENAIAUTHKEY"]

#Initialize app
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#Initialize smtp
create_smtp_conn()

#Handle routes

@app.route('/')
def index():
    return redirect("/home")


@app.route('/home')
def home():
    return render_template('index.html', **session_data())


@app.route('/auth', methods=["GET", "POST"])
def auth():
    if not session.get("auth_email"): #Allow Auth to be available only when requested
        return redirect("/")
    
    if request.method == "GET":
        return render_template('auth.html')
     
    with conn.cursor() as cursor:
        sql = "SELECT * FROM users WHERE email=%s"
        cursor.execute(sql, (session['auth_email'], ))

        result = cursor.fetchone()
        if result is None:
            session.permanent = False
            session.pop("auth_email", None)
            return jsonify("auth failed")
        
        if result['auth'] != request.json.get("auth"):
            return jsonify("auth failed")
        
        #Auth Code matched

        session.permanent = False #No more required to be permanent

        cursor.execute("UPDATE users SET auth=%s, valid=%s WHERE email=%s", (None, 1, result['email']))

        if session.get("forgot"):
            session.pop('forgot', None)
            cursor.execute("UPDATE users SET valid=%s, password=%s WHERE email=%s", (0, None, result['email']))

            return jsonify("password change")
        
        session.pop("auth_email", None)

        for s in ses_keys:
            session[s] = result[s]

        return jsonify("success")
    
    
@app.route('/regenauth')
def regencode():
    if not session.get("auth_email"): #Do not allow this without any auth
        return redirect("/")
    
    auth_email = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    with conn.cursor() as cursor:
        cursor.execute("UPDATE users SET auth=%s WHERE email=%s", (auth_email, session['auth_email']))

    send_email(session['auth_email'], auth_email)

    return redirect("/auth")


@app.route('/login', methods=["GET", "POST"])
def login():
    if session.get("username"):
        return redirect("/")
    
    if request.method == "GET":
        return render_template('login.html')
    
    email = request.json.get("email")
    passwd = request.json.get("password")

    with conn.cursor() as cursor:
        sql = "SELECT * FROM users WHERE email=%s"
        cursor.execute(sql, (email))

        result = cursor.fetchone()
        if result is None:
            return jsonify("login failed")
        
        if result["password"] is None:
            session['auth_email'] = email
            return jsonify("password change")
        
        if result["password"] != passwd:
            return jsonify("login failed")

        if not result['valid']:
            session['auth_email'] = email
            return jsonify("auth required")
        
        session.permanent = request.json.get("checkbox")

        for s in ses_keys:
            session[s] = result[s]

        return jsonify("success")
    

@app.route('/register', methods=["POST", "GET"])
def register():
    if session.get("username"):
        return redirect("/")
    
    if request.method == "GET":
        return render_template('register.html', **session_data())
    
    auth_email = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    data = (
        username, email, password, _, _
    ) = (
        request.json.get("username"), request.json.get("email"), request.json.get("password"),
        auth_email, 0
    )

    try:
        if not username or not email or not password:
            return jsonify("All fields are not filled up.")
        
        if not validate_email(email):
            return jsonify("The given email is not valid.")

        with conn.cursor() as cursor:
            sql = "SELECT * FROM users WHERE email=%s" #Check if exists
            cursor.execute(sql, (email, ))

            if cursor.fetchone():
                return jsonify("An account with this email already exists.")
            
            sql = "INSERT INTO users (username, email, password, auth, valid) VALUES (%s, %s, %s, %s, %s)"
            
            cursor.execute(sql, data)
            
        send_email(email, auth_email)
        
        session['auth_email'] = email
        session.permanent = True
        
        return jsonify("success")
    except Exception as err:
        print(colours.red(err))
        if err.__class__ == SMTPRecipientsRefused:
            
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE email=%s", (email, ))

            return jsonify("The given email is not valid.")
        
        return jsonify("An unexpected error occurred.")
    

@app.route('/generateimage/<prompt>')
def generate(prompt):
    if not session.get("username"):
        return jsonify("unauthorized")
    
    print(colours.blue(f"Prompt [{session['email']}]: {prompt}"))
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=3,
            size='512x512'
        )
        print(colours.green(f"Response: {response}"))
        return jsonify(response)
    except InvalidRequestError as e:
        print(colours.red(e.user_message))
        return jsonify(None)

@app.route('/email', methods=["POST","GET"])
def email():
    if request.method == "GET":
        return render_template('forpwd-email.html')
    
    email = request.json.get("email")

    if not email:
        return jsonify("unknown")

    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE email=%s", (email, ))

        result = cursor.fetchone()

        if result is None:
            return jsonify("unknown")
        
        auth_email = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        with conn.cursor() as cursor:
            sql = "UPDATE users SET auth=%s WHERE email=%s"
            cursor.execute(sql, (auth_email, email))
        
        send_email(email, auth_email)
        
        session['auth_email'] = email
        session['forgot'] = True

        session.permanent = True #Remember
        
        return jsonify("success")
    
@app.route('/change-pwd', methods=["POST","GET"])
def changepwd():
    if not session.get("auth_email"):
        return redirect("/email")

    if request.method == "GET":
        return render_template('chang-pwd.html')
    
    if not new or not old:
        return jsonify("Fields are empty.")
    
    new = request.json.get("new_pass")
    old = request.json.get("old_pass")

    if new != old:
        return jsonify("New and Old passwords do not match.")
    
    with conn.cursor() as cursor:
        sql = "UPDATE users SET password=%s, valid=%s WHERE email=%s"
        cursor.execute(sql, (new, 1, session['auth_email']))

    session.pop("auth_email", None)

    return jsonify("success")

@app.route("/abtus")
def about():
    with open("about-us.txt", "r") as file:
        lines = []
        for line in file.readlines():
            if line.startswith(r"%b"):
                line = line.replace(r"%b", "<b class=enlarge>").replace(":", ":</b>")
            
            lines.append(line)
                
        return render_template("abt-us.html", content='\n'.join(lines))


@app.route('/logout')
def logout():
    if session.get("username"):
        for s in ses_keys:
            session.pop(s, None)
    return redirect("/")

#Run
app.run(host='0.0.0.0', port=5000, debug=True)
