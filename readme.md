
# BFW-Kleinanzeigen

BFW-Kleinanzeigen ist eine Webanwendung im Stil einer internen Kleinanzeigen-Plattform.
Sie entstand im Rahmen meiner Umschulung zum Fachinformatiker für Anwendungsentwicklung am BFW Hamburg und dient als Lernprojekt für:

- Webentwicklung mit Flask
- Template-Rendering mit Jinja2
- Datenbank-Anbindung mit MariaDB/MySQL
- Benutzerverwaltung, Sessions, Rollen & Berechtigungen



## Features

- 👤 **User-Accounts**
  - Registrierung, Login, Logout
  - Passwort-Hashing
- 📋 **Anzeigenverwaltung**
  - Anzeigen erstellen, bearbeiten, löschen
  - Preis, Beschreibung, Kategorie, Bilder
- 🗂️ **Kategorien & Filter**
  - Anzeigen nach Kategorien filtern
  - Startseite mit aktuellen Anzeigen
- 🖼️ **Bilder-Upload**
  - Zuordnung mehrerer Bilder zu einer Anzeige
- 💬 **Internes Nachrichtensystem**
  - Nachrichten zu einer Anzeige schreiben
  - Nachrichten-Inbox für eingeloggte Nutzer:innen
  - Gelesen/Ungelesen-Status
- 🛠️ **Moderator-Rolle**
  - Anzeigen sichten, korrigieren, deaktivieren oder löschen
  - Kategorien verwalten



## Tech-Stack

- **Backend:** Python 3.12, Flask
- **Templating:** Jinja2
- **Datenbank:** MariaDB / MySQL
- **Frontend:** HTML, CSS
- **Sonstiges:** mysql-connector-python, virtualenv



## Installation & Setup

## 1. Repository klonen
```bash
git clone git@github.com:esugre/bfwkleinanzeigen.git
cd bfwkleinanzeigen
````

### 2. Virtuelle Umgebung erstellen

Linux/macOS:

```bash
python3.12 -m venv venv
source venv/bin/activate
```

Windows:

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

## 3. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

---

## 4. Datenbank einrichten

```sql
CREATE DATABASE bfwkleinanzeigen;
CREATE USER 'username'@'localhost' IDENTIFIED BY 'passwort';
GRANT ALL ON bfwkleinanzeigen.* TO 'username'@'localhost';
FLUSH PRIVILEGES;
```

Import:

```bash
sudo mariadb -u username -p bfwkleinanzeigen < sql/schema.sql
sudo mariadb -u username -p bfwkleinanzeigen < sql/categories.sql
sudo mariadb -u username -p bfwkleinanzeigen < sql/messages.sql
```

---

## 5. App starten

```bash
export FLASK_APP=app
flask run
```

Windows:

```powershell
set FLASK_APP=app
flask run
```

App läuft unter:

```
http://127.0.0.1:5000
```

---

## Lernkontext

Dieses Projekt ist ein Ausbildungs-/Lernprojekt zur Vertiefung von Routing, Template‑Struktur, Datenbankzugriff und grundlegenden Sicherheitsaspekten.

