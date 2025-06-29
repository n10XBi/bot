from flask import Flask, render_template
from threading import Thread
from keep_alive import keep_alive
from main import run_bot

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("i.html", active_since="2025-06-28 23:55:00")

def handler(request):
    Thread(target=keep_alive).start()
    Thread(target=run_bot).start()
    return "Bot is running!", 200
