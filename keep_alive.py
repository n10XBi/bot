from flask import Flask, render_template
from threading import Thread
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    active_since = datetime(2025, 6, 1, 8, 0, 0).strftime('%d %B %Y %H:%M:%S')
    return render_template("i.html", active_since=active_since)

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
