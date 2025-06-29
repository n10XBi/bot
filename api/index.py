from flask import Flask, render_template
from threading import Thread
import sys
import os

# Inject path biar bisa impor dari root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import run_bot
from keep_alive import keep_alive

app = Flask(__name__, template_folder="../templates")

@app.route("/")
def home():
    return render_template("i.html", active_since="2025-06-28 23:59:00")

def handler(request):
    Thread(target=keep_alive).start()
    Thread(target=run_bot).start()
    return "Bot is running!", 200
