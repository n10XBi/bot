from main import run_bot  # dari main.py kamu yang sudah diedit
from keep_alive import keep_alive

def handler(request):
    keep_alive()
    run_bot()
    return "Bot is running!", 200
