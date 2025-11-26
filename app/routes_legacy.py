import os
import mysql.connector
from app import app
from flask import Flask, render_template, abort, url_for, request, redirect
from markupsafe import escape, Markup
from werkzeug.utils import secure_filename

# Angabe des Upload-Folders für die Profilbilder der Tiere
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'app','static', 'bilder')
# Größenlimit für die Bilder - 8MB
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024 
# Erlaubte Dateien für den Upload
allowed_extensions = {'png', 'jpg', 'jpeg', 'webp', 'gif'}


#Überprüfungsfunktion ob das hochgeladene File eine zulässige Datei ist, nötig für den Bildupload in pet_new()
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions


#Funktion die eine Verbindung zur Datenbank aufbaut und per Return zur Verfügung stellt. 
def get_db_connection():            
    connection = mysql.connector.connect(
        host=app.config['DB_HOST'],
        user=app.config['DB_USER'],
        password=app.config['DB_PASSWORD'],
        database=app.config['DB_NAME']
    )
    return connection


#Index-Seite - Verschlankt - Alle benötigten Infos in einem Abruf, ohne nachträgliches Filtern mittels Python/Jinja
@app.route('/')
def index():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute('''
                    select
                   p.pet_id,
                   p.name,
                   p.description,
                   p.animal_type,
                   p.owner_id,
                   p.image,
                   exists (
                   select 1
                   from borrowings b
                   where b.pet_id = p.pet_id
                   ) as is_borrowed
                   from pets p
                   order by p.pet_id
                   ''')
    
    pets = cursor.fetchall()
    connection.close()

    return render_template('index.html', pets=pets)


#Login-Seite
@app.route('/login')        
def login():
    
    obrigkeit = '''
    <!doctype html>
    <html lang="de">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Login</title>
    </head>
    <body>
        <h1>Hier findet sich - irgendwann in Zukunft - die Login-Seite</h1> 
    '''

    fußvolk = '''
    <h2>Vielleicht findet sich hier aber auch das Elixir zur Nasenhaarentfernung UND Nasenhaarhinzuführung!!!</h2>
    '''
    userinput1 = "<script>alert('Kaufen Sie heute Ihr exklusives Starterpaket Nasenhaartonikum!!! Buy 1 Pay 2!!!');</script>" #not escaped Userinput
    userinput2 = "Ich bin die traurige escaped Message: <script>alert('Kaufen Sie heute Ihr exklusives Starterpaket Nasenhaartonikum!!! Buy 1 Pay 2!!!');</script>" #escaped Userinput

    output = Markup(obrigkeit) + Markup(userinput1) + escape(userinput2) + Markup(fußvolk)
    return output


#Seite zur Account-Erstellung
@app.route('/register')     
def register():
    return "Hier können Sie sich registrieren."


#Null, aber braucht man für den Logout
@app.route('/logout')       
def logout():
    return "Hier werden Sie abgemeldet."


#User Management Dashboard
@app.route('/admin')
def admin():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('''select
                   user_id, name, role
                   from users''')
    users = cursor.fetchall()
    connection.close()

    return render_template('admin.html', user=users)


#Bearbeiten eines Benutzers
@app.route('/edit_user/<int:user_id>')    
def edit_user(user_id):
    return "Hier findet sich die Nutzerbearbeitung."


#Null, braucht man fürs Löschen eines Nutzers
@app.route('/delete_user/<int:user_id>')    
def delete_user(user_id):
    return "Falls man mal einen Nutzer löschen muss."


# Pet-Details - Verschlankt - Nur noch ein Datensatz der aus der DB abgerufen wird.  
@app.route('/pet/<int:pet_id>')
def pet(pet_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('''
                    select
                   p.pet_id,
                   p.name,
                   p.description,
                   p.animal_type,
                   p.owner_id,
                   p.image,
                   exists (
                   select 1
                   from borrowings b
                   where b.pet_id = p.pet_id
                   ) as is_borrowed
                   from pets p
                   where p.pet_id = %s''',
                   (pet_id,) # execute möchte ein Tupel speisen, also vergesse er nicht ein Komma hinter der Variable, sonst rastet Python aus
                   )
    pet_details = cursor.fetchone()
    connection.close()

    return render_template('pet_details.html', pet=pet_details)
    

# Tier Bearbeiten - Verschlankt - Daten mittels SQL vorsortiert
@app.route('/pet/<int:pet_id>/edit', methods=['GET', 'POST'])
def pet_edit(pet_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('''
                    select
                   name,
                   description,
                   animal_type,
                   owner_id
                   from pets
                   where pet_id = %s''',
                   (pet_id,)
                   )
    
    pet = cursor.fetchone() #V1
    connection.close()

    if request.method == 'POST':
        name = request.form['name']
        animal_type = request.form['animal_type']
        description = request.form['description']

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute('''
                        update pets
                       set name = %s,
                       animal_type = %s,
                       description = %s
                       where pet_id = %s''',
                       (name, animal_type, description, pet_id)
                       )
        connection.commit()
        connection.close()

        #Weiterleitung / Zurück zur Tier-Verwaltung
        return redirect(url_for('pet_management', user_id=pet['owner_id']))
    
    return render_template('pet_edit.html', pet=pet)


#Null, zum Löschen eines Tiers
@app.route('/pet/<int:pet_id>/delete')      
def delete_pet(pet_id):
    return "Falls man mal ein Tier löschen muss."


#Null, zum Ausleihen
@app.route('/pet/<int:pet_id>/borrow')      
def borrow_pet(pet_id):
    return "Wird benötigt wenn man ein Tier ausleihen möchte."


#Null, für die Rückgabe
@app.route('/pet/<int:pet_id>/return')      
def return_pet(pet_id):
    return "Wird für die Rückgabe benötigt."


# Tierverwaltung - Verschlankt - Information direkt per SQL wie benötigt, statt mittels Python Loops after Loops...
@app.route('/pet-management/<int:user_id>')
def pet_management(user_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('''
                    select
                        p.pet_id,
                        p.name,
                        p.animal_type,
                        case
                            when exists (
                                select 1
                                from borrowings b
                                where b.pet_id = p.pet_id
                                ) 
                                then 'verliehen'
                                else 'verfügbar'
                            end as status
                   from pets p
                   where p.owner_id = %s''',
                   (user_id,)
                   )
    
    own_pets = cursor.fetchall() #V1 für Übersicht meiner Tiere und nur diese o_^
    
    cursor.execute('''
                    select
                        p.pet_id,
                        p.name,
                        p.animal_type,
                        p.owner_id
                    from pets p
                    where pet_id in (
                    select pet_id
                    from borrowings
                    where borrower_id = %s)''',
                    (user_id,)
                    )

    borrowed_pets = cursor.fetchall() #V2 für Übersicht meiner ausgeliehenen Tiere
    connection.close()

    return render_template('pet-management.html', own_pets=own_pets, borrowed_pets=borrowed_pets)


#Seite zum Anlegen neuer Tiere
@app.route('/pet/new/<int:user_id>', methods=['GET', 'POST']) #Brauche hier eig. gar keine Get-Method     
def pet_new(user_id):

    if request.method == 'POST':

        name = request.form['name']
        animal_type = request.form['animal_type']
        description = request.form['description']

        #Standardmäßig kein Bild
        image = None

        #Bildupload - die Verwirrung ist groß
        file = request.files['image']
        if file and file.filename:
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)

                #Ok, nochmal gucken ob der Ordner überhaupt existiert
                upload_folder = app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)

                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)

                #Als String abspeichern
                image = f"bilder/{filename}"
            
        #Speichern in der Datenbank
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute('''
                        insert into pets (
                            name, animal_type, description, owner_id, image)
                            Values (%s, %s, %s, %s, %s)
                        ''', (name, animal_type, description, user_id, image)
                        )
        
        connection.commit()
        connection.close()


        #Weiterleitung / Zurück zur Tier-Verwaltung
        return redirect(url_for('pet_management', user_id=user_id))

    else:
        return render_template('pet_new.html')

#Fallback auf die angelegte Fehlerseite
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

