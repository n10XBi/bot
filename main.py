# (omitted for brevity - same as earlier cell)
from flask import Flask, request, render_template
from threading import Thread
from telethon import TelegramClient, events, Button
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telethon.errors import UsernameNotOccupiedError, PeerIdInvalidError
import os, asyncio, warnings
from datetime import datetime
active_since = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# Konfigurasi akun dan bot
api_id = 23661233
api_hash = '0e211a8335e923bf46ca18be8db7aa09'
session_name = 'session_mykenangan'
bot_token = '7831869839:AAGbPyISg7xclVJkRucFcxIpFkDP-zdZdwg'
AUTHORIZED_USERS = {8196980814, 7041100577}
BACKUP_CHANNEL = -1002715846418

# Flask app untuk keep alive dan antarmuka
app = Flask(__name__)

@app.route('/')
def index():
    return render_template("i.html", active_since=active_since)

# Mulai Flask secara paralel
def keep_alive():
    t = Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
    t.start()

# Init Telethon
user_client = TelegramClient(session_name, api_id, api_hash)
bot = TelegramClient('bot_session', api_id, api_hash)

scanned_messages = []
scan_message_ids = []

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def get_media_type(msg):
    if isinstance(msg.media, MessageMediaPhoto):
        return "📷 Foto"
    elif isinstance(msg.media, MessageMediaDocument):
        if msg.file and msg.file.mime_type:
            if 'video' in msg.file.mime_type:
                return "🎥 Video"
            elif 'audio' in msg.file.mime_type:
                return "🎵 Audio"
            else:
                return "📄 Dokumen"
        return "📄 Dokumen"
    return "❓ Lainnya"

async def scan_target_chat(target):
    try:
        if target.startswith("/scan"):
            target = target.replace("/scan", "").strip()
        entity = await user_client.get_entity(target)
        name = getattr(entity, 'title', getattr(entity, 'first_name', 'TanpaNama'))
        async for msg in user_client.iter_messages(entity, reverse=True):
            if msg.media and isinstance(msg.media, (MessageMediaPhoto, MessageMediaDocument)):
                size = getattr(msg.media.document, 'size', 0) if isinstance(msg.media, MessageMediaDocument) else 0
                media_type = get_media_type(msg)
                date = msg.date.strftime('%Y-%m-%d %H:%M:%S')
                scanned_messages.append({
                    'chat': name,
                    'id': msg.id,
                    'entity': entity,
                    'message': msg,
                    'size': size,
                    'type': media_type,
                    'date': date
                })
        return name
    except (UsernameNotOccupiedError, PeerIdInvalidError):
        return f"[!] Nomor tidak ditemukan: {target}"
    except Exception as e:
        return f"[!] Gagal scan: {e}"

@bot.on(events.NewMessage(pattern='/scan'))
async def handle_scan(event):
    if event.sender_id not in AUTHORIZED_USERS:
        return
    message = event.raw_text.strip()
    if len(message.split()) < 2:
        await event.respond("📱 Kirim nomor target setelah perintah, contoh: /scan +628xxxxxx")
        return
    target = message.split(None, 1)[1]
    scanned_messages.clear()
    name = await scan_target_chat(target)
    if not scanned_messages:
        await event.respond(f"❌ Tidak ada media ditemukan dari {name}.")
        return
    info_text = f"📄 Menemukan {len(scanned_messages)} media dari {name}:\n"
    for i, item in enumerate(scanned_messages):
        info_text += f"{i+1}. ID {item['id']} - {item['type']} - {format_size(item['size'])} - 🕒 {item['date']}\n"
    info_text += "\n📝 Kirim nomor urutan (misal: 1 atau 2,3) untuk mengunduh."
    msg = await event.respond(info_text, buttons=[Button.inline("🧹 Selesai & Hapus", data="done")])
    scan_message_ids.append(msg.id)

@bot.on(events.NewMessage(pattern=r'^[0-9,\s]+$'))
async def handle_download(event):
    if event.sender_id not in AUTHORIZED_USERS:
        return
    indexes = [int(x.strip()) - 1 for x in event.text.split(',') if x.strip().isdigit()]
    for i in indexes:
        if 0 <= i < len(scanned_messages):
            item = scanned_messages[i]
            msg = item['message']
            os.makedirs("downloads", exist_ok=True)
            await event.respond(f"⬇️ Mengunduh ID {item['id']} ({item['type']} {format_size(item['size'])})...")
            try:
                path = await user_client.download_media(msg, file="downloads/")
                if path:
                    buttons = [[Button.inline("📤 Backup ke Channel", data=f"backup|{path}")]]
                    await bot.send_file(
                        event.chat_id,
                        path,
                        caption=f"✅ Disimpan: {os.path.basename(path)}\n📝 Klik tombol untuk backup ke channel kamu.",
                        buttons=buttons
                    )
                else:
                    await event.respond("❌ File tidak ditemukan setelah diunduh.")
            except Exception as e:
                await event.respond(f"❌ Gagal download: {e}")

@bot.on(events.CallbackQuery(data=lambda d: d.startswith(b'backup|')))
async def handle_backup_button(event):
    if event.sender_id not in AUTHORIZED_USERS:
        return
    path = event.data.decode().split('|', 1)[1]
    if not os.path.exists(path):
        await event.respond("❌ File tidak ditemukan untuk backup.")
        return
    try:
        await bot.send_file(
            BACKUP_CHANNEL,
            path,
            caption=f"🗂️ Backup otomatis via bot\n📎 Nama: {os.path.basename(path)}"
        )
        await event.respond("✅ Berhasil di-backup ke channel privat.")
    except Exception as e:
        await event.respond(f"❌ Gagal mengirim ke channel: {e}")

@bot.on(events.CallbackQuery(data=b'done'))
async def handle_done(event):
    if event.sender_id not in AUTHORIZED_USERS:
        return
    for msg_id in scan_message_ids:
        try:
            await bot.delete_messages(event.chat_id, msg_id)
        except:
            pass
    scan_message_ids.clear()
    await event.respond("✅ Semua pesan hasil scan telah dihapus.")

async def main():
    keep_alive()
    await user_client.start()
    await bot.start(bot_token=bot_token)
    print("🤖 Bot hybrid aktif!")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        asyncio.get_event_loop().run_until_complete(main())
