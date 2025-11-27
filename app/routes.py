from flask import (
    render_template, request, redirect, url_for,
    flash, session
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from app import app
import mysql.connector
import os
from werkzeug.utils import secure_filename


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
#   Datei-Upload Hilfsfunktion
# ---------------------------
# Die erlaubten Dateien aus der Config holen
ALLOWED_EXTENSIONS = app.config.get('ALLOWED_EXTENSIONS')

def allowed_file(filename: str):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    """Prüft, ob die hochgeladene Datei erlaubt ist und nutzen secure_filename um sicherzustellen,
    dass der Dateiname nicht irgendeinen Murks/Sonderzeichen enthält."""


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
@app.route('/') # Alle Anzeigen auf der Startseite
def index():
    """
    Startseite mit allen Anzeigen. Romi rendert dann daraus das Listing der Anzeigen."""

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        select 
            ads.ad_id,
            ads.titel,
            ads.text,
            ads.preis,
            ads.datum,
            ads.status,
            ads.bilder_path,
            users.vorname,
            users.nachname
        from ads
        join users on ads.owner_id = users.user_id
        order by ads.datum desc
        """
    )

    ads = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('index.html', ads=ads)  # Übergabe an die Front, do whatever you want wif it! ;)


# ---------------------------
#   Nutzer - Listings
# ---------------------------
@app.route('/my-ads')   # Anzeigen des eingeloggten Nutzers
@login_required
def my_ads():
    """
    Zeigt alle Anzeigen des aktuell eingloggten Nuters an.
    - Filter über owner_id = session['user_id']
    - Daten gehen an das Template my_ads.html als Variable 'ads'
    """

    owner_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Hier nuckeln wir nur die Anzeigen des eingeloggten Nutzers
    # Join mit users brauchen wir hier nicht, wir wissen ja wer wir sind, hoff ich ;)
    cursor.execute(
        """
        select
            ads.ad_id,
            ads.owner_id,
            ads.titel,
            ads.text,
            ads.preis,
            ads.datum,
            ads.status,
            ads.bilder_path
        from ads
        whereads.owner_id = %s
        order by ads.datum desc
        """,
        (owner_id,)
    )
    ads = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Feierliche Übergabe an Romis Template
    return render_template('my_ads.html', ads=ads)

# ---------------------------
#   Registrierung
# ---------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    # POST-Teil
    vorname = request.form.get('vorname')
    nachname = request.form.get('nachname')
    email = request.form.get('email')
    password = request.form.get('password')

    if not vorname or not nachname or not email or not password:
        flash("Bitte alle Felder ausfüllen.")
        return redirect(url_for('register'))

    hashed_pw = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO users (vorname, nachname, email, passwort_hash, rolle)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (vorname, nachname, email, hashed_pw, "user")
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

    email = request.form.get('email')
    password = request.form.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE email = %s",
        (email,)
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user and check_password_hash(user['passwort_hash'], password):
        session['user_id'] = user['user_id']         # Spalte heißt user_id
        session['email'] = user['email']
        session['vorname'] = user['vorname']
        session['nachname'] = user['nachname']
        flash("Erfolgreich eingeloggt.")
        return redirect(url_for('index'))
    else:
        flash("Ungültige E-Mail oder Passwort.")
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
#   Neue Anzeige erstellen
# ---------------------------
@app.route('/ads/new', methods=['GET', 'POST'])
@login_required
def ad_new():
    """Neue Route zum Erstellen einer neuen Anzeige mit Bild-Upload.
    - Get zeigt das Formular an.
    - Post verarbeitet die Formulardaten + Bild und speichert sie in der DB."""

    # Wenn die Seite per Get aufgerufen wird, zeigt sie das Formular an
    if request.method == 'GET':
        return render_template('ads_new.html')
    
    # Formulardaten auslesen
    titel = request.form.get('titel')
    text = request.form.get('text')
    preis_opt = request.form.get('preis') # besser als optionales Feld

    # Check ob alles ausgefüllt wurde
    if not titel or not text:
        flash("Bitte alle Felder ausfüllen.")
        return redirect(url_for('ad_new'))


    # Wenn ein Preis angegeben wurde, gleich typecasten
    preis = None
    if preis_opt:
        try:
            preis = float(preis_opt.replace(',', '.')) # Damit kann man auch ein Komma nutzen
        except ValueError:
            flash("Bitte einen gültigen Preis angeben.")
            return redirect(url_for('ad_new'))
    
    # Jetzt noch den Besitzer der Anzeige aus der Session holen
    owner_id = session.get('user_id')

    # Jetzt noch die Bilder verarbeiten
    # "images" ist der Name des File-Input-Felds im Formular // name="" im <input type="file">
    files = request.files.getlist('images')

    # Liste der Pfade der gespeicherten Bilder
    saved_paths = []

    # Pfad zum Uploads-Ordner - siehe Config
    upload_folder_relativ = app.config['UPLOAD_FOLDER'] 
    upload_folder_absolut = os.path.join(app.root_path, upload_folder_relativ) 

    # Wenn der Ordner nicht existiert, erstellen
    os.makedirs(upload_folder_absolut, exist_ok=True)

    # Jetzt müssen wir erstmal durch jede hochgeladene Datei durchgehen
    for file in files:
        # Wenn keine Bilder ausgewählt wurden, können wir das überspringen
        if not file or not file.filename:
            continue

        # Checken ob das überhaupt ein erlaubtes Dateiformat ist
        if not allowed_file(file.filename):
            flash(f"Datei '{file.filename}' hat ein nicht erlaubtes Format.")
            continue

        # Basteln uns neue saubere Dateinamen
        filename = secure_filename(file.filename)

        # Hängen noch zusätzlich die owner_id an den Dateinamen
        filename = f"{owner_id}_{filename}"

        # Absoluten Pfad zum Speichern der Datei
        absoluter_pfad = os.path.join(upload_folder_absolut, filename)

        # Datei auf dem Webserver speichern
        file.save(absoluter_pfad)

        # Relativer Pfad wie wir ihn im Template auch später mit <img src="..."> nutzen
        # zb "static/uploads/23_bildvonbanane.jpg"
        relativer_pfad = os.path.join(upload_folder_relativ, filename).replace("\\", "/")
        saved_paths.append(relativer_pfad) # Wir speichern den relativen Pfads in der DB

    
    # Jetzt alles in die DB speichern
    conn = get_db_connection()
    cursor = conn.cursor()

    # Das erste Bild als Hauptbild für die Anzeige nutzen, also wenn eins existiert
    hauptbild = saved_paths[0] if saved_paths else None

    # Eintrag in die ads-Tabelle gemäß Schema
    cursor.execute(
        """
        insert into ads (owner_id, titel, text, preis, bilder_path)
        values (%s, %s, %s, %s, %s)
        """,
        (owner_id, titel, text, preis, hauptbild)
    )

    # Jetzt holen wir uns noch die ad_id der gerade erstellten Anzeige (auto increment), 
    # damit wir die Bilder in der ad_images Tabelle speichern können
    ad_id = cursor.lastrowid

    # Bilder in der ad_images Tabelle speichern
    # Jede Datei bekommt einen eigenen Eintrag mit sort_order
    for sort_order, relativer_pfad in enumerate(saved_paths, start=1): # Start 1, damit das erste Bild nicht [0] ist. 
        cursor.execute(
            """
            insert into ad_images (ad_id, file_path, sort_order)
            values (%s, %s, %s)
            """,
            (ad_id, relativer_pfad, sort_order)
        )

    # Speichern in der Datenbank abschließen
    conn.commit()
    cursor.close()  
    conn.close()

    # Noch Feedback an den Nutzer und zurück zur Startseite
    flash("Anzeige erfolgreich erstellt!")
    return redirect(url_for('index'))


# ---------------------------
#   404 Fehlerseite
# ---------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# ---------------------------
#   Session-Testseite
# ---------------------------
@app.route('/secret')
@login_required
def secret():
    return "Nur für Eingeloggte"


