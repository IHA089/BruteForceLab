import logging
from flask import Flask, request, render_template, session, jsonify, redirect, url_for
from functools import wraps
import sqlite3
import hashlib
import random, string
import os, requests, urllib3

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

lab_type = "AccountTakeover"
lab_name = "BruteForceLab"

flag_data = {}

BruteForce = Flask(__name__)
BruteForce.secret_key = "vulnerable_lab_by_IHA089"

def generate_flag(length=10):
    charset = string.ascii_letters + string.digits
    random_string = ''.join(random.choices(charset, k=length))
    return random_string

def create_database():
    db_path = os.path.join(os.getcwd(), lab_type, lab_name, 'users.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gmail TEXT NOT NULL,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        active TINYINT(1) DEFAULT 0,
        code TEXT NOT NULL
    )
    ''')

    numb = random.randint(100, 999)
    passw = "admin@"+str(numb)
    passw_hash = hashlib.md5(passw.encode()).hexdigest()
    query = "INSERT INTO users (gmail, username, password, active, code) VALUES ('admin@iha089.org', 'admin', '"+passw_hash+"', '1', '45AEDF32')"
    cursor.execute(query)
    conn.commit()
    conn.close()

def generate_code():
    first_two = ''.join(random.choices(string.digits, k=2))
    next_four = ''.join(random.choices(string.ascii_uppercase, k=4))
    last_two = ''.join(random.choices(string.digits, k=2))
    code = first_two + next_four + last_two
    return code

def check_database():
    db_path = os.path.join(os.getcwd(), lab_type, lab_name, 'users.db')
    if not os.path.isfile(db_path):
        create_database()

check_database()

def get_db_connection():
    db_path=os.path.join(os.getcwd(), lab_type, lab_name, 'users.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@BruteForce.route('/')
def home():
    return render_template('index.html')

@BruteForce.route('/index.html')
def index_html():
    return render_template('index.html', user=session.get('user'))

@BruteForce.route('/login.html')
def login_html():
    return render_template('login.html')

@BruteForce.route('/join.html')
def join_html():
    return render_template('join.html')

@BruteForce.route('/acceptable.html')
def acceptable_html():
    return render_template('acceptable.html', user=session.get('user'))

@BruteForce.route('/check.html')
def check_html():
    return render_template('check.html', user=session.get('user'))

@BruteForce.route('/term.html')
def term_html():
    return render_template('term.html', user=session.get('user'))

@BruteForce.route('/privacy.html')
def privacy_html():
    return render_template('privacy.html', user=session.get('user'))    

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:  
            return redirect(url_for('login_html', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@BruteForce.route('/confirm', methods=['POST'])
def confirm():
    username = request.form.get('username')
    password = request.form.get('password')
    code = request.form.get('confirmationcode')
    hash_password=hashlib.md5(password.encode()).hexdigest()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT *FROM users WHERE username = ? or gmail = ? AND password=? AND code = ?", (username, username, hash_password, code))
    user = cursor.fetchone()
    
    if user:
        cursor.execute("UPDATE users SET active = 1 WHERE username = ? or gmail = ?", (username, username))
        conn.commit()
        conn.close()
        session['user'] = username
        return redirect(url_for('dashboard'))
    
    conn.close()
    error_message = "Invalid code"
    return render_template('confirm.html', error=error_message, username=username, password=password)

@BruteForce.route('/check', methods=['POST'])
def check():
    session_code = request.form.get('sessioncode')
    ss_code = []
    if 'admin@iha089.org' in flag_data:
        ss_code.append(flag_data['admin@iha089.org'])

    if 'admin' in flag_data:
        ss_code.append(flag_data['admin'])

    if session_code in ss_code:
        return render_template('success.html', user=session.get('user'))
    else:
        return render_template('check.html', error="wrong session code")


@BruteForce.route('/resend', methods=['POST'])
def resend():
    username = request.form.get('username')
    password = request.form.get('password')
    hash_password=hashlib.md5(password.encode()).hexdigest()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM users WHERE username = ? or gmail = ? AND password = ?", (username, username, hash_password))
    code = cursor.fetchone()
    if code:
        username=username
        username = username.replace(" ", "")
        bdcontent = "<h2>Verify Your Account password</h2><p>your verification code are given below</p><div style=\"background-color: orange; color: black; font-size: 14px; padding: 10px; border-radius: 5px; font-family: Arial, sans-serif;\">"+code[0]+"</div><p>If you did not request this, please ignore this email.</p>"
        mail_server = "https://127.0.0.1:7089/dcb8df93f8885473ad69681e82c423163edca1b13cf2f4c39c1956b4d32b4275"
        payload = {"email": username,
                    "sender":"IHA089 Labs ::: BruteForceLab",
                    "subject":"BruteForceLab::Verify Your Accout",
                    "bodycontent":bdcontent
                }
        try:
            k = requests.post(mail_server, json = payload, verify=False)
            print(k.text)
        except Exception as e:
            print(e)
            return jsonify({"error": "Mail server is not responding"}), 500
        error_message="code sent"
    else:
        error_message="Invalid username or password"

    conn.close()
    return render_template('confirm.html', error=error_message, username=username, password=password)

@BruteForce.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()
    hash_password = hashlib.md5(password.encode()).hexdigest()
    cursor.execute("SELECT * FROM users WHERE username = ? or gmail = ? AND password = ?", (username, username, hash_password))
    user = cursor.fetchone()
    conn.close()

    if user:
        if not user[4] == 1:
            return render_template('confirm.html', username=username, password=password)
        session['user'] = username
        return redirect(url_for('dashboard'))
    error_message = "Invalid username or password. Please try again."
    return render_template('login.html', error=error_message)

@BruteForce.route('/join', methods=['POST'])
def join():
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')
    if not email.endswith('@iha089.org'):
        error_message = "Only email with @iha089.org domain is allowed."
        return render_template('join.html', error=error_message)
    conn = get_db_connection()
    cursor = conn.cursor()
    hash_password = hashlib.md5(password.encode()).hexdigest()
    code = generate_code()
    query = f"INSERT INTO users (gmail, username, password, active, code) VALUES ('{email}', '{username}', '{hash_password}', '0', '{code}')".format(email, username, hash_password, code)
    cursor.execute("SELECT * FROM users where gmail = ?", (email,))
    if cursor.fetchone():
        error_message = "Email already taken. Please choose another."
        conn.close()
        return render_template('join.html', error=error_message)
    else:
        try:
            cursor.execute(query)
            conn.commit()
            username=email
            username = username.replace(" ", "")
            bdcontent = "<h2>Verify Your Account password</h2><p>your verification code are given below</p><div style=\"background-color: orange; color: black; font-size: 14px; padding: 10px; border-radius: 5px; font-family: Arial, sans-serif;\">"+code+"</div><p>If you did not request this, please ignore this email.</p>"
            mail_server = "https://127.0.0.1:7089/dcb8df93f8885473ad69681e82c423163edca1b13cf2f4c39c1956b4d32b4275"
            payload = {"email": username,
                        "sender":"IHA089 Labs ::: BruteForceLab",
                        "subject":"BruteForceLab::Verify Your Accout",
                        "bodycontent":bdcontent
                    }
            try:
                k = requests.post(mail_server, json = payload, verify=False)
            except:
                return jsonify({"error": "Mail server is not responding"}), 500

            return render_template('confirm.html', username=email, password=password)
        except sqlite3.Error as err:
            error_message = "Something went wrong, Please try again later."
            return render_template('join.html', error=error_message)
        conn.close()  

@BruteForce.route('/dashboard')
@BruteForce.route("/dashboard.html")
@login_required
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login_html'))
    username = session.get('user')
    if username not in flag_data:
        flag_data[username] = generate_flag()

    flag_code = flag_data[username]

    return render_template('dashboard.html', user=session.get('user'), flag=flag_code)

@BruteForce.route('/logout.html')
def logout():
    session.clear() 
    return redirect(url_for('login_html'))

@BruteForce.route('/profile')
@BruteForce.route('/profile.html')
@login_required
def profile():
    if 'user' not in session:
        return redirect(url_for('login_html'))
    return render_template('profile.html', user=session.get('user'))

@BruteForce.after_request
def add_cache_control_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
