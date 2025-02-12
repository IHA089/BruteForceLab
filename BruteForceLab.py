import logging
from flask import Flask, request, render_template, session, jsonify, redirect, url_for
from functools import wraps
from dnslib.server import DNSServer, DNSLogger
from dnslib.dns import QTYPE, RR, A
import sqlite3
import hashlib
import threading

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.secret_key = "vulnerable_lab by IHA089"

def check_database():
    pwd = os.getcwd()
    path = pwd+"/users.db"

    if not os.path.isfile(path):
        import setup_database
        setup_database.create_database()

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/index.html')
def index_html():
    return render_template('index.html', user=session.get('user'))

@app.route('/login.html')
def login_html():
    return render_template('login.html')

@app.route('/join.html')
def join_html():
    return render_template('join.html')

@app.route('/acceptable.html')
def acceptable_html():
    return render_template('acceptable.html', user=session.get('user'))

@app.route('/term.html')
def term_html():
    return render_template('term.html', user=session.get('user'))

@app.route('/privacy.html')
def privacy_html():
    return render_template('privacy.html', user=session.get('user'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:  
            return redirect(url_for('login_html', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()
    hash_password = hashlib.md5(password.encode()).hexdigest()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hash_password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user'] = username
        return redirect(url_for('dashboard'))
    error_message = "Invalid username or password. Please try again."
    return render_template('login.html', error=error_message)

@app.route('/join', methods=['POST'])
def join():
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')
    conn = get_db_connection()
    cursor = conn.cursor()
    hash_password = hashlib.md5(password.encode()).hexdigest()
    query = f"INSERT INTO users (gmail, username, password) VALUES ('{email}', '{username}', '{hash_password}')".format(email, username, password)
    cursor.execute("SELECT * FROM users where gmail = ?", (email,))
    if cursor.fetchone():
        error_message = "Email already taken. Please choose another."
        conn.close()
        return render_template('join.html', error=error_message)
    else:
        try:
            cursor.execute(query)
            conn.commit()
            return render_template('login.html')
        except sqlite3.Error as err:
            error_message = "Something went wrong, Please try again later."
            return render_template('join.html', error=error_message)
        conn.close()
    

@app.route('/dashboard')
@app.route("/dashboard.html")
@login_required
def dashboard():
    print(session['user'])
    if 'user' not in session:
        return redirect(url_for('login_html'))
    admin_list=['admin', 'administrator']
    if session.get('user') in admin_list:
        return render_template('admin-dashboard.html', user=session.get('user'))

    return render_template('dashboard.html', user=session.get('user'))

@app.route('/logout.html')
def logout():
    session.clear() 
    return redirect(url_for('login_html'))

@app.route('/profile')
@app.route('/profile.html')
@login_required
def profile():
    if 'user' not in session:
        return redirect(url_for('login_html'))
    return render_template('profile.html', user=session.get('user'))


@app.after_request
def add_cache_control_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

def start_flask_server():
    check_database()
    app.run(host='127.0.0.1', port=7089, debug=False, use_reloader=False) 

