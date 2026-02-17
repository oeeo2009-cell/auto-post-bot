
# telegram @m50cl
from pyrogram import Client, filters, idle
from pyrogram.types import (
    Message, CallbackQuery, ForceReply,
    InlineKeyboardMarkup as Markup,
    InlineKeyboardButton as Button
)
from pyrogram.errors import UserNotParticipant, ChatWriteForbidden
from pyrolistener import Listener, exceptions
from asyncio import create_task, sleep, get_event_loop
from datetime import datetime, timedelta
from pytz import timezone
import json, os

# ================== CONFIG ==================
app = Client(
    "autoPost",
    api_id=27845947,          # ضع API ID
    api_hash="a137701a731dacfc4a2e205d44d3a4bc",    # ضع API HASH
    bot_token="8588445925:AAGxaleDaUoLu-MBJDjmpPgQUPggSduCiIE"  # توكن البوت
)

owner = 8303099506  # ايديك
loop = get_event_loop()
listener = Listener(app)

users_db = "users.json"
channels_db = "channels.json"

# ================== STORAGE ==================
def write(fp, data):
    with open(fp, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def read(fp, default):
    if not os.path.exists(fp):
        write(fp, default)
    with open(fp) as f:
        return json.load(f)

users = read(users_db, {})
channels = read(channels_db, [])

# ================== UI ==================
homeMarkup = Markup([
    [Button("📌 حسابك", callback_data="account")],
    [Button("📨 الرد التلقائي", callback_data="autoReply")],
    [Button("▶️ بدء النشر", callback_data="startPosting"),
     Button("⏹ إيقاف النشر", callback_data="stopPosting")]
])

# ================== START ==================
@app.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    uid = str(message.from_user.id)
    if uid not in users:
        users[uid] = {
            "vip": True if message.from_user.id == owner else False,
            "groups": [],
            "caption": "",
            "waitTime": 60,
            "posting": False,
            "auto_reply": False,
            "auto_reply_text": "مرحبا 🌹\nحاليا غير متواجد، سأرد عليك لاحقًا."
        }
        write(users_db, users)

    await message.reply(
        "🤖 أهلا بك في بوت النشر التلقائي\nاختر من الأزرار:",
        reply_markup=homeMarkup
    )

# ================== AUTO REPLY ==================
@app.on_callback_query(filters.regex("^autoReply$"))
async def auto_reply_menu(_, cb: CallbackQuery):
    uid = str(cb.from_user.id)
    status = "مفعل ✅" if users[uid]["auto_reply"] else "متوقف ❌"

    markup = Markup([
        [Button("✅ تفعيل", callback_data="enableAR"),
         Button("❌ تعطيل", callback_data="disableAR")],
        [Button("✏️ تعيين الرسالة", callback_data="setAR")],
        [Button("🔙 رجوع", callback_data="home")]
    ])

    await cb.message.edit_text(
        f"📨 الرد التلقائي\n\nالحالة: {status}",
        reply_markup=markup
    )

@app.on_callback_query(filters.regex("^enableAR$"))
async def enable_ar(_, cb: CallbackQuery):
    uid = str(cb.from_user.id)
    users[uid]["auto_reply"] = True
    write(users_db, users)
    await cb.answer("تم تفعيل الرد التلقائي ✅", show_alert=True)

@app.on_callback_query(filters.regex("^disableAR$"))
async def disable_ar(_, cb: CallbackQuery):
    uid = str(cb.from_user.id)
    users[uid]["auto_reply"] = False
    write(users_db, users)
    await cb.answer("تم تعطيل الرد التلقائي ❌", show_alert=True)

@app.on_callback_query(filters.regex("^setAR$"))
async def set_ar(_, cb: CallbackQuery):
    uid = str(cb.from_user.id)
    await cb.message.delete()
    try:
        msg = await listener.listen(
            from_id=cb.from_user.id,
            chat_id=cb.from_user.id,
            text="✏️ أرسل رسالة الرد التلقائي:",
            reply_markup=ForceReply(selective=True),
            timeout=60
        )
    except exceptions.TimeOut:
        return
    users[uid]["auto_reply_text"] = msg.text
    write(users_db, users)
    await msg.reply("✅ تم حفظ رسالة الرد التلقائي")

# ================== AUTO REPLY HANDLER ==================
@app.on_message(filters.private & ~filters.me)
async def auto_reply_handler(_, message: Message):
    uid = str(message.to_user.id)
    if uid in users and users[uid]["auto_reply"]:
        await message.reply(users[uid]["auto_reply_text"])

# ================== POSTING ==================
@app.on_callback_query(filters.regex("^startPosting$"))
async def start_posting(_, cb: CallbackQuery):
    uid = str(cb.from_user.id)
    if users[uid]["posting"]:
        return await cb.answer("النشر يعمل بالفعل", show_alert=True)
    users[uid]["posting"] = True
    write(users_db, users)
    create_task(posting(cb.from_user.id))
    await cb.answer("تم بدء النشر ▶️", show_alert=True)

@app.on_callback_query(filters.regex("^stopPosting$"))
async def stop_posting(_, cb: CallbackQuery):
    uid = str(cb.from_user.id)
    users[uid]["posting"] = False
    write(users_db, users)
    await cb.answer("تم إيقاف النشر ⏹", show_alert=True)

async def posting(user_id):
    uid = str(user_id)
    client = Client(
        uid,
        api_id=app.api_id,
        api_hash=app.api_hash,
        session_string=users[uid].get("session")
    )
    try:
        await client.start()
    except:
        return

    while users[uid]["posting"]:
        for group in users[uid]["groups"]:
            try:
                await client.send_message(group, users[uid]["caption"])
            except ChatWriteForbidden:
                pass
        await sleep(users[uid]["waitTime"])

    await client.stop()

# ================== HOME ==================
@app.on_callback_query(filters.regex("^home$"))
async def home(_, cb: CallbackQuery):
    await cb.message.edit_text(
        "القائمة الرئيسية",
        reply_markup=homeMarkup
    )

# ================== RUN ==================
async def main():
    await app.start()
    await idle()

if __name__ == "__main__":
    loop.run_until_complete(main())
