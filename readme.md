# BFW-Kleinanzeigen

BFW-Kleinanzeigen ist eine Webanwendung im Stil einer internen Kleinanzeigen-Plattform.  
Sie entstand im Rahmen meiner Umschulung zum Fachinformatiker für Anwendungsentwicklung am BFW Hamburg und dient als Lernprojekt für:

- Webentwicklung mit Flask
- Template-Rendering mit Jinja2
- Datenbank-Anbindung mit MariaDB/MySQL
- Benutzerverwaltung, Sessions, Rollen & Berechtigungen

---

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
- 🛠️ **Moderator-Rolle (Online-Redaktion)**
  - Anzeigen sichten, korrigieren, deaktivieren oder löschen
  - Kategorien verwalten (anlegen, umbenennen, deaktivieren)

---

## Tech-Stack

- **Backend:** Python 3.12, Flask
- **Templating:** Jinja2
- **Datenbank:** MariaDB / MySQL
- **Frontend:** HTML, CSS (klassische Templates, kein SPA)
- **Sonstiges:** `mysql-connector-python`, virtualenv

---

## Installation & Setup (lokal)

### 1. Repository klonen

```bash
git clone git@github.com:esugre/bfwkleinanzeigen.git
cd bfwkleinanzeigen
