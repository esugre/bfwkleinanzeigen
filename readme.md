# BFW-Kleinanzeigen

## 1. Repo klonen

```bash
git clone git@gitlab.bfwhh-service.de:razapf/bfw-kleinanzeigen.git
cd bfw-kleinanzeigen
```

## 2. Umgebung einrichten / aktivieren

Linux:
```bash
python3.12 -m venv venv
source venv/bin/activate
```
unter Windows:
```bash
python3.12 -m venv venv
.\venv\Scripts\activate
```

## 3. Abhängigkeiten installieren

```bash
pip install flask
pip install mysql-connector-python
```

## 4. Datenbank einrichten

### Unter Linux
MariaDB
```bash
sudo systemctl start mariadb
sudo mariadb -u root -p
```

Datenbank und Benutzer anlegen
```sql
create database bfwkleinanzeigen;

create user 'username'@'localhost' identified by 'deinpasswort';

grant all on bfwkleinanzeigen.* to 'username'@'localhost';

exit;
```

Das Datenbank-Schema importieren:
Wieder ins Projektverzeichnis wechseln und dort das Terminal starten:
```bash
sudo mariadb -u username -p bfwkleinanzeigen < sql/schema.sql
```
Zusätzlich noch die Kategorien importieren:
```bash
sudo mariadb -u username -p bfwkleinanzeigen < sql/categories.sql
```
Eine Erweiterung noch holen:
```bash
sudo mariadb -u username -p bfwkleinanzeigen < sql/messages.sql
```

### Unter Windows mit XAMPP

Dienste starten:
- XAMPP starten
- MySQL starten
- Admin-Button bei MySQL öffnet phpMyAdmin im Browser

Datebank über phpMyAdmin anlegen:
- Oben im Menü auf "Neu" klicken
- Name: bfwkleinanzeigen
- Rest einfach so lassen

Benutzer anlegen über SQL-Befehl (einfacher):
```sql
create user 'username'@'localhost' identified by 'deinpasswort';
grant all on bfwkleinanzeigen.* to 'username'@'localhost';
```

Datenbankschema importieren:
- in phpMyAdmin die neue Datenbank auswählen
- oben auf importieren klicken
- Die schema.sql aus dem repo auswählen
- unten auf importieren klicken

## 5. Konfiguration anpassen
Im Repo gibt es eine config.example.py, in der deine Datenbankverbindungsdaten hinterlegt werden.
Diese kopieren und in config.py umbenennen sowie deine Daten anpassen. 
Diese mittels .gitignore nicht pushen. 
```python
SECRET_KEY = "CHANGE_ME" # Nicht vergessen das wir denselben nutzen!
DB_HOST = "localhost"
DB_NAME = "bfwkleinanzeigen"
DB_USER = "username"
DB_PASSWORD = "deinpasswort"
```

## 6. Starten der App

```bash
# Virtuelle Umgebung aktivieren
source venv/bin/activate # Linux
.\venv\Scripts\activate # Windows

# App starten
python hello-flask.py
```
Sollte nun auf Port 5000 erreichbar sein.