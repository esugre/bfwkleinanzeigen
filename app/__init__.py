from flask import Flask

app = Flask(__name__)

# Config laden
app.config.from_pyfile('config.py')

# Jetzt erst die Routes importieren
from app import routes