from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import os

CHANNEL_USERNAME = "@Johirul_Islam_Taskin"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"স্বাগতম, {update.effective_user.first_name}!\n\n"
        f"অনুগ্রহ করে আমাদের চ্যানেল সাবস্ক্রাইব করুন: {CHANNEL_USERNAME}"
    )

async def get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["member", "administrator", "creator"]:
            await update.message.reply_text("অনুগ্রহ করে একটি URL দিন যেটার সোর্স কোড দেখতে চান:")
            context.user_data['awaiting_url'] = True
        else:
            raise Exception("Not subscribed")
    except:
        await update.message.reply_text(f"আপনি এখনও {CHANNEL_USERNAME} চ্যানেলটি সাবস্ক্রাইব করেননি!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_url'):
        url = update.message.text
        if url.startswith("http://") or url.startswith("https://"):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                source_code = response.text[:4000]
                await update.message.reply_text("ওয়েবসাইটের কিছু অংশের সোর্স কোড:\n\n" + source_code)
            except:
                await update.message.reply_text("URL টি অ্যাক্সেস করা যাচ্ছে না বা ভুল URL!")
        else:
            await update.message.reply_text("দয়া করে একটি সঠিক URL দিন (http/https সহ)।")
        context.user_data['awaiting_url'] = False
    else:
        await update.message.reply_text("এই কমান্ডটি আমি চিনতে পারিনি।")

if __name__ == '__main__':
    from telegram.ext import Application
    from flask import Flask, request

    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    APP_URL = os.environ.get("APP_URL")  # Render-এর External URL

    flask_app = Flask(__name__)
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get", get))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    @flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
    def telegram_webhook():
        update = Update.de_json(request.get_json(force=True), app.bot)
        app.update_queue.put_nowait(update)
        return "ok"

    async def main():
        await app.bot.set_webhook(url=f"{APP_URL}/{BOT_TOKEN}")
        print("Webhook set!")

    import threading
    threading.Thread(target=lambda: app.run_polling(allowed_updates=Update.ALL_TYPES)).start()

    import asyncio
    asyncio.run(main())

    flask_app.run(host="0.0.0.0", port=10000)
