from flask import (
    render_template, request, redirect, url_for,
    flash, session
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from app import app
import mysql.connector


# ---------------------------
#   Datenbankverbindung
# ---------------------------
def get_db_connection():
    connection = mysql.connector.connect(
        host=app.config['DB_HOST'],
        user=app.config['DB_USER'],
        password=app.config['DB_PASSWORD'],
        database=app.config['DB_NAME']
    )
    return connection


# ---------------------------
#   Login Required Decorator
# ---------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Bitte erst einloggen.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ---------------------------
#   Startseite
# ---------------------------
@app.route('/')
def index():
    return render_template('index.html')  # Platzhalter, später Liste der Anzeigen


# ---------------------------
#   Registrierung
# ---------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    # Post-PArt
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash("Bitte alle Felder ausfüllen.")
        return redirect(url_for('register'))
    
    hashed_pw = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
        (username, hashed_pw)
    )
    conn.commit()
    cursor.close()
    conn.close()

    flash("Konto erfolgreich erstellt! Bitte einloggen.")
    return redirect(url_for('login'))



# ---------------------------
#   Login
# ---------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    #Post-Part
    username = request.form.get('username')
    password = request.form.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE username = %s",
        (username,)
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        return redirect(url_for('index'))
    else:
        flash("Ungültige Login-Daten.")
        return redirect(url_for('login'))



# ---------------------------
#   Logout
# ---------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Erfolgreich ausgeloggt.")
    return redirect(url_for('index'))


# ---------------------------
#   404 Fehlerseite
# ---------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
