import json
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import ZoneInfo
import pytz

load_dotenv()
# Replace with your actual bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8443))  # Default to 8443 if not set
WEBHOOK_URL = f"https://{os.environ['RENDER_SERVICE_NAME']}.onrender.com/{BOT_TOKEN}"
MY_CHAT_ID = int(os.getenv("MY_CHAT_ID"))

my_timezone = ZoneInfo("Asia/Kathmandu")
current_time = datetime.datetime.now(tz=my_timezone)

# Load routine from file
def load_routine():
    with open("routine.json", "r", encoding="utf-8") as file:
        return json.load(file)

# /today command handler
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    routine = load_routine()
    weekday = current_time.strftime('%A')
    classes = routine.get(weekday, [])
    today_time = current_time.date()
    out = f"**📅{weekday}**\n"
    if not classes['classes']:
        await update.message.reply_text("🎉 No classes today!")
        await tomorrow(update, context)
    else:
        start_time_str = classes.get("start_time", "10:15:00")
        start_time = datetime.datetime.strptime(start_time_str, "%H:%M:%S").time()
        current_start = datetime.datetime.combine(today_time, start_time).replace(tzinfo=my_timezone)
        msg = f"📚 Classes for Today -->{weekday}:\n\n"
        for sub, kind, duration  in classes["classes"]:
            subject = routine.get(sub, sub)
            begin_time = current_start
            end_time = begin_time + datetime.timedelta(minutes=duration*routine['class_time'])
            time = f"{begin_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
            current_start = end_time
            class_type = f"{routine.get(kind[0], kind[0])} "
            for k in range(1, len(kind)):
                class_type += f"+ {routine.get(kind[k], kind[k])} "
            msg += f"• {subject}\n  {class_type}\n  🕒{time}\n  ⏳{duration} Periods({duration*routine['class_time']} mins) \n\n"
        await update.message.reply_text(msg)


async def upcoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    routine = load_routine()
    weekday = current_time.strftime("%A")
    classes = routine.get(weekday, [])
    today = current_time.date()
    rem = 0

    if not classes:
        await update.message.reply_text("🎉 No classes for today.")
        await tomorrow(update, context)
    else:
        start_time_str = classes.get("start_time", "10:15:00")
        start_time = datetime.datetime.strptime(start_time_str, "%H:%M:%S").time()
        current_start = datetime.datetime.combine(today, start_time).replace(tzinfo=my_timezone)
        msg = f"📅 Next class for today → {weekday}:\n"

        for sub, kind, duration in classes["classes"]:
            subject = routine.get(sub, sub)

            begin_time = current_start
            end_time = begin_time + datetime.timedelta(minutes=duration*routine['class_time'])

            # ✅ Use 24-hour format explicitly
            time_str = f"{begin_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
            print(time_str)
            current_start = end_time  # move to next class's start time
            # Class type formatting
            class_type = f"{routine.get(kind[0], kind[0])}"
            for k in range(1, len(kind)):
                class_type += f" + {routine.get(kind[k], kind[k])}"

            # print("DEBUG -->", datetime.datetime.now(),  begin_time, end_time)
            # print(datetime.datetime.combine(today, (datetime.datetime.strptime("13:37:00", "%H:%M:%S")).time()))
            if (current_time < end_time) and (current_time< begin_time):
                # print("in the loop")
                rem += 1
                msg += f"\n• {subject}\n  {class_type}\n   🕒 {time_str}\n  ⏳{duration} Periods({duration*routine['class_time']} mins)\n"
             
        if rem == 0:
            msg += f"\n🎉 Classes finished for today → {weekday}."
            await update.message.reply_text(msg)
            await tomorrow(update, context)
            return

        await update.message.reply_text(msg)



async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    routine = load_routine()
    weekday = (current_time + datetime.timedelta(days=1)).strftime("%A")
    classes = routine.get(weekday, [])
    tomo = current_time.date() + datetime.timedelta(days=1)

    if not classes:
        await update.message.reply_text(f"🎉 No classes for tomorrow -->{weekday}.\nEnjoy your holiday 🎉")
    else:
        start_time = datetime.datetime.combine(tomo, datetime.datetime.strptime(classes.get("start_time", "10:15:00"), '%H:%M:%S').time()).replace(tzinfo=my_timezone)  
        msg = f"📚 Classes for Tomorrow-{weekday}\n\n"
        for sub, kind, duration in classes['classes']:
            subject = routine.get(sub, sub)
            begin_time = start_time
            end_time = (begin_time + datetime.timedelta(minutes=duration*routine['class_time']))
            time = f"{begin_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
            start_time = end_time

            class_type = f"{routine.get(kind[0], kind[0])} "
            for k in range(1, len(kind)):
                class_type += f"+ {routine.get(kind[k], kind[k])} "
            msg += f"• {subject}\n  {class_type}\n  🕒{time}\n  ⏳{duration} Periods({duration*routine['class_time']} mins)\n\n"
        
        await update.message.reply_text(msg)


async def ongoing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    routine= load_routine()
    weekday = current_time.strftime("%A")
    today = (current_time.date())
    classes = routine.get(weekday, [])
    print("DEBUG -->", today)

    if not classes:
        await update.message.reply_text("🎉 No classes for today.")
        await tomorrow(update, context)
        return
    
    start_time = datetime.datetime.combine(today, datetime.datetime.strptime(classes.get("start_time", "10:15:00"), '%H:%M:%S').time()).replace(tzinfo=my_timezone)
    for sub, kind, duration in classes['classes']:
        subject = routine.get(sub, sub)
        begin_time = start_time
        end_time = begin_time + datetime.timedelta(minutes=duration * routine['class_time'])
        time_str = f"{begin_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
        start_time = end_time
        await update.message.reply_text(f"DEBUG --> {str(current_time)},{subject}, { begin_time},{ end_time}")

        if ((current_time >= begin_time) and (current_time <= end_time)):
            class_type = f"{routine.get(kind[0], kind[0])} "
            for k in range(1, len(kind)):
                class_type += f"+ {routine.get(kind[k], kind[k])} "
            msg = f"📚 Ongoing Class:\n\n• {subject}\n  {class_type}\n  🕒{time_str}\n  ⏳{int((end_time-current_time).total_seconds()//60)} mins remaining\n"
            await update.message.reply_text(msg)
            return

    if current_time > start_time:
        await update.message.reply_text(f"🎉 Classes Finished for Today -->{weekday}.")
        await tomorrow(update, context)
        return
    
    await update.message.reply_text(f"🎉 No ongoing classes your next class starts at {begin_time.strftime('%H:%M')}.")
    return


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📌 *Available Commands:*\n\n"
        "/today - Show today's classes\n"
        "/tomorrow - Show tomorrow's classes\n"
        "/next - Show next class for today\n"
        "/ongoing - Show ongoing class\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! I am your bot.')

# Scheduled job
async def send_daily_routine():
    print("⏰ Sending daily routine...")
    await app.bot.send_message(chat_id=MY_CHAT_ID, text=today(update=Update, context=ContextTypes.DEFAULT_TYPE), parse_mode="Markdown")

# Main function to run the bot
async def main():
    global app
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("next", upcoming))
    app.add_handler(CommandHandler("tomorrow", tomorrow))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ongoing", ongoing))
    print("✅ Bot running. \n 📌 *Available Commands:*\n"
        "/today - Show today's classes\n"
        "/tomorrow - Show tomorrow's classes\n"
        "/next - Show next class for today\n"
        "/ongoing - Show ongoing class\n"
        "/help - Show this help message")
    
    await app.initialize()
    await app.bot.set_webhook(WEBHOOK_URL)
    await app.start()

    await app.updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=WEBHOOK_URL
    )
    scheduler = AsyncIOScheduler(timezone=my_timezone)
    scheduler.add_job(send_daily_routine, CronTrigger(hour=22, minute=10))  # Change time as needed
    scheduler.start()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
