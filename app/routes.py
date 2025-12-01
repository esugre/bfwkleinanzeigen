from flask import (
    render_template, request, redirect, url_for,
    flash, session, current_app, abort, jsonify
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
#   Category-Helper-Function
# ---------------------------
def get_all_categories(cursor):
    cursor.execute("""
                    select category_id, name
                   from categories
                   order by category_id asc
                   """)
    return cursor.fetchall()


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
#   Search Endpunkt
# ---------------------------
@app.route('/search')
def search():

    """
        Sucht in ads.titel + ads.text
        GET /search?search_term=...
        gibt komplette Anzeigenobjekte zurück (mit owner & categories)
        Übergabe als json für JS-Fetch
    """

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    search_term = request.args.get('search_term', '').strip()

    if not search_term:
        return jsonify([])
    
    like = f"%{search_term}%"

    cursor.execute("""
                select 
                    a.ad_id,
                    a.owner_id,
                    a.titel,
                    a.text,
                    a.preis,
                    a.status,
                    a.datum,
                    a.bilder_path,
                    u.vorname,
                    u.nachname
                from ads as a
                join users as u on u.user_id = a.owner_id
                where
                    a.status = "aktiv"
                and
                    (upper(a.titel) like upper(%s)
                    or upper(a.text) like upper(%s))
                order by
                    a.datum desc
                   """,
                   (like, like)
                   )
    ads = cursor.fetchall()

    # Profilaktisch Kategorien pro Anzeige mitgeben, sollte mir langsam eine Funktion dafür schreiben...
    ad_ids = [ad['ad_id'] for ad in ads]
    ad_categories_map = {}

    if ad_ids:
        ids_str = ','.join(str(_id) for _id in ad_ids)

        cursor.execute("""
                    select
                       ac.ad_id,
                       c.category_id,
                       c.name
                    from ads_categories as ac
                    join categories as c on c.category_id = ac.category_id
                    where ac.ad_id in ({ids_str})
                       """)
        
        rows = cursor.fetchall()
        for row in rows:
            ad_categories_map.setdefault(row['ad_id'], []).append({
                'category_id': row['category_id'],
                'name': row['name'],
            })

    for ad in ads:
        ad['categories'] = ad_categories_map.get(ad['ad_id'], [])
    
    return jsonify(ads)


# ---------------------------
#   Startseite/Index-Site
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
        where ads.status = "aktiv"
        order by ads.datum desc
        """
    )

    ads = cursor.fetchall()

    # Kategorien noch aus der Datenbank holen für Sidebar/Navi oder so
    all_categories = get_all_categories(cursor)

    # Da Anzeigen mehrere Kategorien haben können, alle Kategorien pro ad nachladen
    ad_ids = [ad['ad_id'] for ad in ads]
    ad_categories_map = {}

    if ad_ids:
        ids_str = ",".join(str(_id) for _id in ad_ids)

        abfrage = f"""
                    select
                    ac.ad_id,
                    c.category_id,
                    c.name
                    from ads_categories as ac
                    join categories as c on c.category_id = ac.category_id
                    where ac.ad_id in ({ids_str})
                    order by c.name asc
                    """
        cursor.execute(abfrage)
        dataset = cursor.fetchall()

        for row in dataset:
            ad_id = row['ad_id']
            ad_categories_map.setdefault(ad_id, []).append({
                'category_id': row['category_id'],
                'name': row['name'],
            })
    
    # Kategorien an die Anzeige mit dranhängen
    for ad in ads:
        ad['categories'] = ad_categories_map.get(ad['ad_id'], [])

    cursor.close()
    conn.close()

    return render_template('index.html', ads=ads, categories=all_categories)  # Übergabe an die Front, do whatever you want wif it! ;)


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
        where ads.owner_id = %s
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
#   Kategorie-Filter-Route (public)
# ---------------------------
@app.route('/category/<int:category_id>')
def ads_by_category(category_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Die jeweilige Kategorie aus dem Äther saugen
    cursor.execute("""
                    select category_id, name
                   from categories
                   where category_id = %s
                   """,
                   (category_id,)
                   )
    category = cursor.fetchone()

    if category is None:
        abort(404) # Endlich mal auf die schöne Fehlerseite verweisen

    # Trotzdem die restlichen Kategorien holen, damit man diese in die Navi oder irgendeine Seitenleiste einpflegen kann
    all_categories = get_all_categories(cursor)

    # Alle Anzeigen die der ausgewählten Kategorie zugeordnet sind
    cursor.execute("""
                    select
                        a.ad_id,
                        a.owner_id,
                        a.titel,
                        a.text,
                        a.preis,
                        a.status,
                        a.datum,
                        a.bilder_path,
                        u.vorname,
                        u.nachname
                   from ads as a
                   join ads_categories as ac on ac.ad_id = a.ad_id
                   join users as u on u.user_id = a.owner_id
                   where ac.category_id = %s
                   and a.status = "aktiv"
                   order by a.datum desc
                   """,
                   (category_id,)
                   )
    ads = cursor.fetchall()

    # Für Tags noch Kategorien pro Ad
    ad_ids = [ad['ad_id'] for ad in ads] # Erstmal alle ad_ids in eine Liste schafueln
    ad_categories_map = {} 

    if ad_ids:
        # anzahl platzhalter = anzahl ids
        placeholder_list = ['%s'] * len(ad_ids)
        placeholder = ','.join(placeholder_list) # brauchen wir gleich für die abfrage
        abfrage = f"""
                    select 
                        ac.ad_id,
                        c.category_id,
                        c.name
                    from ads_categories as ac
                    join categories as c on c.category_id = ac.category_id
                    where ac.ad_id in ({placeholder})
                    order by c.name asc
                    """
        cursor.execute(abfrage, tuple(ad_ids))
        dataset = cursor.fetchall()

        for set in dataset:
            ad_id =set['ad_id']
            ad_categories_map.setdefault(ad_id, []).append({
                'category_id': set['category_id'],
                'name': set['name'],
            })
    
    # Kategorien in die Anzeige schieben
    for ad in ads:
        ad['categories'] = ad_categories_map.get(ad['ad_id'], [])
    
    return render_template(
        'category_ads.html',
        ads=ads,
        active_category=category,
        categories=all_categories
    )


# ---------------------------
#   Ad-Detail-Site
# ---------------------------
@app.route('/ads/<int:ad_id>')
def ad_detail(ad_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Anzeige mit all ihren Details laden
    cursor.execute("""
                    select
                   a.ad_id,
                   a.owner_id,
                   a.titel,
                   a.text,
                   a.preis,
                   a.status,
                   a.datum,
                   a.bilder_path,
                   u.vorname,
                   u.nachname,
                   u.email
                   from ads as a
                   join users as u on u.user_id = a.owner_id
                   where a.ad_id = %s
                   """,
                   (ad_id,)
                   )
    ad = cursor.fetchone()

    if ad is None:
        abort(404)

    rolle = session.get('rolle')
    current_user_id = session.get('user_id')

    if ad['status'] != "aktiv":
        # Nur Owner oder Admin/Redakteur:in dürfen nicht aktive Anzeigen sehen
        if current_user_id != ad['owner_id'] and rolle not in ('admin', 'redakteur'):
            abort(404)

    # Jetzt noch die weiteren Pfade zu den Bilder der Anzeige aus der ad_images Tabelle holen
    cursor.execute("""
                    select 
                   image_id,
                   file_path,
                   sort_order,
                   uploaded_at
                   from ad_images
                   where ad_id = %s
                   order by sort_order asc, uploaded_at asc
                   """,
                   (ad_id,)
                   )
    images = cursor.fetchall()
    
    # Kategorien der Anzeige
    cursor.execute("""
                    select 
                   c.category_id,
                   c.name
                   from ads_categories as ac
                   join categories as c on c.category_id = ac.category_id
                   where ac.ad_id = %s
                   order by c.name asc
                   """,
                   (ad_id,)
                   )
    ad_categories = cursor.fetchall()

    # Und noch alle Kategorien, just for the sake of it
    all_categores = get_all_categories(cursor)

    # Kategorien an das Objekt hängen (nur für bessere Konsistenz der Daten)
    ad['categories'] = ad_categories

    # Feierliche Übergabe an Romis Template
    return render_template(
        'ad_detail.html', 
        ad=ad,
        images = images,
        categories = all_categores #die "globale" Kategorienliste
        )


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
        session['user_id'] = user['user_id']         
        session['email'] = user['email']
        session['vorname'] = user['vorname']
        session['nachname'] = user['nachname']
        session['rolle'] = user['rolle']
        session['logged_in'] = True
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
    - Kategorien vorher noch aus der Datenbank holen
    - Post verarbeitet die Formulardaten + Bild und speichert sie in der DB."""

    # Wenn die Seite per Get aufgerufen wird, zeigt sie das Formular an
    if request.method == 'GET':
        #DB-Verbindung
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        #Kategorien abholen
        cursor.execute("""
                        select category_id, name 
                       from categories
                       order by category_id asc
                       """)
        categories = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('ads_new.html', categories=categories)
    
    # Formulardaten auslesen
    titel = request.form.get('titel')
    text = request.form.get('text')
    preis_opt = request.form.get('preis') # besser als optionales Feld
    category_ids_raw = request.form.getlist('categories')

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
    
    # Jetzt noch den Anzeigen-Besitzer und seine Rolle aus der Session holen
    owner_id = session.get('user_id')
    rolle = session.get('rolle', 'user')

    # Unterscheidung user/admin bzw. Redakteur:in
    # Normaler user -> Anzeigen-Status "pending"
    # Admin/Redakteur -> direkt Anzeigen-Status "aktiv"
    if rolle in ('admin', 'redakteur'):
        status = "aktiv"
    else:
        status = "pending"

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
        insert into ads (owner_id, titel, text, preis, status, bilder_path)
        values (%s, %s, %s, %s, %s, %s)
        """,
        (owner_id, titel, text, preis, status, hauptbild)
    )

    # Jetzt holen wir uns noch die ad_id der gerade erstellten Anzeige (auto increment), 
    # damit wir die Bilder in der ad_images Tabelle speichern können
    ad_id = cursor.lastrowid

    # Noch die mit dieser Ad verknüpften Kategorien in die ads_categories eintragen 
    category_ids = []
    for cid in category_ids_raw:
        try:
            category_ids.append(int(cid))
        except ValueError:
            continue

    for cid in category_ids:
        cursor.execute("""
                        insert into ads_categories 
                       (ad_id, category_id) 
                       values (%s, %s)
                       """,
                       (ad_id, cid)
                       )

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
#   Anzeige löschen
# ---------------------------
@app.route('/ads/<int:ad_id>/delete', methods=['GET','POST'])
@login_required
def delete_ad(ad_id):

    # Erstmal die Anzeige holen, wenn möglich:
    user_id = session.get('user_id')
    if not user_id:
        flash("Bitte logge dich zuerst ein!", "error")
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Kurzcheck ob das überhaupt des Nutzers Anzeige ist
    cursor.execute("""
                    select owner_id from ads where ad_id =%s
                   """,
                   (ad_id,)
                   )
    ad = cursor.fetchone()

    # Berechtigungen checken
    current_user_id = session.get('user_id')
    rolle = session.get('rolle')

    if not ad or (ad['owner_id'] != current_user_id and rolle not in ('admin', 'redakteur')):
        flash("Sorry, die Anzeige wurde leider nicht gefunden oder du hast keine Berechtigung dazu.", "error")
        return redirect(url_for('my_ads'))
    
    # Pfade der lokal gespeicherten Bilder aus der Datenbank holen (ad_images)
    cursor.execute("""
                    select file_path from ad_images where ad_id = %s
                   """,
                   (ad_id,)
                   )
    image_rows = cursor.fetchall()

    # Liste mit extrahierten Bildpfaden:
    file_paths = {row['file_path'] for row in image_rows}

    # Bilder lokal löschen
    base_dir = current_app.root_path # Sowas wie /home/user/bfw-kleinanzeigen

    for rel_path in file_paths:
        full_path = os.path.join(base_dir, rel_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except Exception:
                pass
    
    # Ad-Datensatz löschen -> delete on cascade löscht automatisch:
        # alle Bild-Datensätze aus ad_images
        # alle Kategorienzuordnungen 
    cursor.execute("""
                    delete from ads where ad_id = %s
                   """, (ad_id,)
                   )
    conn.commit()
    cursor.close()
    conn.close()


    flash("Die Anzeige wurde erfolgreich gelöscht!", "success")
    return redirect(url_for('my_ads'))


# ---------------------------
#   Anzeige bearbeiten
# ---------------------------
@app.route('/ads/<int:ad_id>/edit', methods=['GET', 'POST'])
@login_required
def ad_edit(ad_id):
    """
    Zum Bearbeiten der Anzeige (natürlich nur vom Besitzer der Anzeige).
    get:
        - Anzeige laden
        - alle dazu gehörenden Bilder laden
        - Infos + Bilder gehen ans Frontend
    post:
        - Titel, Text, Preis, usw. holen
        - Vom Formular ids sammeln um ggf. Bilddateien als auch DB-Einträge zu löschen
        - Ggf. neue Bilder speichern und in ad_image eintragen
        - Konsistenz beim Cover -> holen wir uns ja nebst ad_images aus ads.bilder_path
        - Wenn also das bisherige gelöscht wurde -> neues auswählen
        - Gab es zuvor keine und es wurden Bilder hochgeladen, das erste neue als Cover nehmen.
    """

    # Fuck me, das wird viel zu umfangreich... egal
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Erstmal wieder die Anzeige aus der Datenbank holen
    cursor.execute("""
                    select ad_id, owner_id, titel, text, preis, status, bilder_path
                   from ads
                   where ad_id = %s
                   """,
                   (ad_id,)
                   )
    ad = cursor.fetchone()

    if not ad:
        cursor.close()
        conn.close()
        flash("Die Anzeige wurde nicht gefunden!", "error")
        return redirect(url_for('my_ads'))
    
    # Berechtigungen checken
    current_user_id = session.get('user_id')
    rolle = session.get('rolle')

    if ad['owner_id'] != current_user_id and rolle not in ('admin', 'redakteur'):
        cursor.close()
        conn.close()
        flash("Diggi, das ist nicht deine Anzeige!", "error")
        return redirect(url_for('my_ads'))
    
    # Bilderpfade der Anzeige holen
    cursor.execute("""
                    select image_id, file_path, sort_order, uploaded_at
                   from ad_images
                   where ad_id = %s
                   order by sort_order asc
                    """,
                    (ad_id,)
    )

    images = cursor.fetchall()

    # Noch die Kategorien dazuholen
    cursor.execute("""
                    select category_id, name
                   from categories
                   order by category_id asc
                   """)
    all_categories = cursor.fetchall()

    # Dieser Anzeige zugeordnete Kategorien holen
    cursor.execute("""
                    select category_id
                   from ads_categories
                   where ad_id = %s
                   """,
                   (ad_id,)
                   )

    selected_rows = cursor.fetchall()
    selected_category_ids = {row['category_id'] for row in selected_rows}

    ###### GET #####
    # über get den ganzen Shizzle-Kadizzle anzeigen
    if request.method == 'GET':
        cursor.close()
        conn.close()
        # Übergabe an Template mit Anzeigeninfos + Liste aller Bilder
        return render_template(
            'ad_edit.html', 
            ad=ad, 
            images=images, 
            categories=all_categories,
            selected_category_ids=selected_category_ids
            )
    
    ##### POST #####
    # Formulardaten auslesen
    titel = request.form.get('titel')
    text = request.form.get('text')
    preis_raw = request.form.get('preis')
    status = request.form.get('status')
    category_ids_raw = request.form.getlist('categories')

    if not titel or not text:
        cursor.close()
        conn.close()
        flash("Also wenigstens einen Titel und eine Beschreibung dazu bitte!", "error")
        return redirect(url_for('ad_edit', ad_id=ad_id))
    
    # Preis Punkt-Komma-Gestöhne
    preis = None
    if preis_raw:
        try:
            preis = float(preis_raw.replace(',', '.'))
        except ValueError:
            cursor.close()
            conn.close()
            flash("Was auch immer du da eingegeben hast, eine Zahl ist das nicht!", "error")
            return redirect(url_for('ad_edit', ad_id=ad_id))
    
    if not status:
        status = ad['status']

    # Als nächstes updaten wir jetzt diese ganzen Infos aus dem Formular (except le pictures)
    cursor.execute("""
                    update ads
                   set  titel = %s,
                        text = %s,
                        preis = %s,
                        status = %s
                   where ad_id = %s
                    """,
                    (titel, text, preis, status, ad_id,)
                    )

    # Kategorien entfernen/hinzufügen
    # alte Einträge entfernen
    cursor.execute("""
                    delete from ads_categories 
                   where ad_id = %s
                   """,
                   (ad_id,)
                   )
    
    # neue Einträge/Änderungen hinzufügen
    category_ids = []
    for cid in category_ids_raw:
        try:
            category_ids.append(int(cid))
        except ValueError:
            continue

    for cid in category_ids:
        cursor.execute("""
                        insert into ads_categories (ad_id, category_id)
                       values (%s, %s)
                       """,
                       (ad_id, cid,)
                       )

    # Ok, als nächstes kümmern wir uns um die zu löschenden Bilder (ausgewählt mittels Checkbox im Formular)
    # Das kann im Formular ungefähr so aussehen:
    # <input type="checkbox", name="delete_images" value="{{ image.image_id }}">
    to_delete_ids = request.form.getlist('delete_images') # Hier haben wir shcon mal die image_id's der Bilder
    images_to_delete = []

    if to_delete_ids:
        #Typecasten in int
        try:
            to_delete_ids = [int(x) for x in to_delete_ids]
        except ValueError:
            to_delete_ids = []

    if to_delete_ids:
        #Platzhalter für "%s, %s, %s" generieren
        strings = ','.join(['%s'] * len(to_delete_ids))

        # Pfade extrahieren der zu löschenden Bilder
        cursor.execute(f"""
                        select image_id, file_path
                       from ad_images
                       where image_id in ({strings})
                        and ad_id = %s
                       """,
                       (*to_delete_ids, ad_id,)
                       )
        images_to_delete = cursor.fetchall()

######

        # Jetzt noch die DB-Einträge aus ad_images löschen
        cursor.execute(f"""
                        delete from ad_images where image_id in ({strings})
                        and ad_id = %s
                        """,
                        (*to_delete_ids, ad_id,)
                        )
    
    # Schon total den Überblick verloren, ah ja die ggf. neuen Bilder müssen ja auch noch
    # hinzugefügt werden
    ########### NEW PICS ###########
    files = request.files.getlist('images') # Analog zum Anlegen einer neuen Anzeige: 
                                            # <input name='images' multiple> in dem edit Formular

    upload_folder_rel = app.config['UPLOAD_FOLDER']            
    upload_folder_abs = os.path.join(app.root_path, upload_folder_rel)
    os.makedirs(upload_folder_abs, exist_ok=True)

    # sort_order, warum.. klingt bei der Konzeption sinnvoll, macht Arbeit hier im Hinterstübchen
    # also was ist die aktuelle max sort_order?
    cursor.execute("""
                    select coalesce(max(sort_order), 0) as max_sort
                   from ad_images
                   where ad_id = %s
                   """,
                   (ad_id,)
                   )
    row = cursor.fetchone()
    current_max_sort = row['max_sort'] if row else 0

    new_sort = current_max_sort
    new_image_paths = [] # falls wir ein neues cover-bild in ads.bilder_path haben

    for file in files:
        if not file or not file.filename:
            continue

        if not allowed_file(file.filename):
            flash(f"Bild '{file.filename}' hat leider kein erlaubtes Bildformat und wurde geschasst.")
            continue

        filename =  secure_filename(file.filename)
        filename = f"{session.get('user_id')}_{filename}"

        abs_path = os.path.join(upload_folder_abs, filename)
        file.save(abs_path)

        rel_path = os.path.join(upload_folder_rel, filename).replace('\\', '/')
        new_image_paths.append(rel_path)

        new_sort += 1
        cursor.execute("""
                        insert into ad_images (ad_id, file_path, sort_order)
                       values (%s, %s, %s)
                       """,
                       (ad_id, rel_path, new_sort,)
                       )
        
    ##### Cover-Bild #####
    # Zwei Möglichkeiten
    # Cover-Bild war gesetzt, könnte aber gelöscht worden sein
    # Cover-Bild war leer, aber jetzt haben wir Bilder...
    # Vorgehen:
    # - Wenns noch Bilder gibt, einfach das mit dem kleinsten sort_order nehmen
    # - wenn es keine Bilder mehr gibt, bilder_path auf NULL setzen

    cursor.execute("""
                    select file_path
                   from ad_images
                   where ad_id = %s
                   order by sort_order asc
                   limit 1
                   """,
                   (ad_id,)
                   )
    cover_row = cursor.fetchone()

    if cover_row:
        new_cover = cover_row['file_path']
    else:
        new_cover = None

    cursor.execute("""
                    update ads
                   set bilder_path = %s
                   where ad_id = %s
                   """,
                   (new_cover, ad_id,)
                   )

    conn.commit()
    cursor.close()
    conn.close()

        # Bilder auf dem Server löschen
    for img in images_to_delete:
        rel_path = img['file_path'] # wäre dann zb 'static/uploads/2_bananenbild.jpg'
        abs_path = os.path.join(app.root_path, rel_path)
        try:
            if os.path.exists(abs_path):
                os.remove(abs_path)
        except OSError:
            # Nicht wild wenn das Bild schon weg ist
            pass

    flash("Heureka, deine Anzeige wurde aktualisiert,\n wenn du wüsstest wie viel Arbeit das hinter den Kullissen ist")
    return redirect(url_for('my_ads')) #Noch nicht existent, aber vorbereitend, sonst find ich das nicht mehr ;)


# ---------------------------
#   Admin/Redakteur:in Moderation (new pending Ads)
# ---------------------------
@app.route('/admin/ads/pending')
@login_required
def admin_pending_ads():
    if session.get('rolle') not in ('admin', 'redakteur'):
        abort(403)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
                    select
                   a.ad_id,
                   a.owner_id,
                   a.titel,
                   a.text,
                   a.preis,
                   a.status,
                   a.datum,
                   a.bilder_path,
                   u.vorname,
                   u.nachname
                   from ads as a
                   join users as u on u.user_id = a.owner_id
                   where a.status = "pending"
                   order by a.datum asc
                   """)

    ads = cursor.fetchall()
    
    return render_template('admin_pending_ads.html', ads=ads)
    # Kleine Tabelle mit Titel, User, Datum, Buttons Freischalten/Löschen 
    # Anklickbar -> ad_detail - Site


# ---------------------------
#   Admin/Redakteur:in Freischalt-Route
# ---------------------------
@app.route('/admin/ads/<int:ad_id>/approve', methods=['POST'])
@login_required
def admin_approve_ad(ad_id):
    if session.get('rolle') not in ('admin', 'redakteur'):
        abort(403)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
                    update ads set status = "aktiv" where ad_id = %s
                   """, 
                   (ad_id,)
                   )
    
    conn.commit()

    flash("Anzeige wurde freigeschaltet.", "success")
    return redirect(url_for('admin_pending_ads'))


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


