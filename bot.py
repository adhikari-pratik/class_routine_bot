import json
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv

load_dotenv()
# Replace with your actual bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8443))  # Default to 8443 if not set
WEBHOOK_URL = f"https://{os.environ['RENDER_SERVICE_NAME']}.onrender.com/{BOT_TOKEN}"

# Load routine from file
def load_routine():
    with open("routine.json", "r", encoding="utf-8") as file:
        return json.load(file)

# /today command handler
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    routine = load_routine()
    weekday = datetime.datetime.now().strftime('%A')
    classes = routine.get(weekday, [])

    if not classes['classes']:
        await update.message.reply_text("🎉 No classes today!")
        await tomorrow(update, context)
    else:
        start_time = classes.get("start_time", "10:15:00")
        msg = f"📚 Classes for Today -->{weekday}:\n\n"
        for sub, kind, duration  in classes["classes"]:
            subject = routine.get(sub, sub)

            begin_time = (datetime.datetime.strptime(start_time, '%H:%M:%S'))
            end_time = (datetime.datetime.strptime(start_time, '%H:%M:%S') + datetime.timedelta(minutes=duration*routine['class_time'])).time()
            time = f"{begin_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
            start_time = str(end_time)
            class_type = f"{routine.get(kind[0], kind[0])} "
            for k in range(1, len(kind)):
                class_type += f"+ {routine.get(kind[k], kind[k])} "
            msg += f"• {subject}\n  {class_type}\n  🕒{time}\n  ⏳{duration} Periods({duration*routine['class_time']} mins) \n\n"
        await update.message.reply_text(msg)


async def upcoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    routine = load_routine()
    weekday = datetime.datetime.now().strftime("%A")
    classes = routine.get(weekday, [])
    today = datetime.date.today()
    rem = 0

    if not classes['classes']:
        await update.message.reply_text("🎉 No classes for today.")
        await tomorrow(update, context)
    else:
        start_time_str = classes.get("start_time", "10:15:00")
        start_time = datetime.datetime.strptime(start_time_str, "%H:%M:%S").time()
        current_start = datetime.datetime.combine(today, start_time)
        msg = f"📅 Next class for today → {weekday}:\n"
        start_time = datetime.datetime.strptime(classes.get("start_time", "10:15:00"), '%H:%M:%S').time()
        current_start = datetime.datetime.combine(today, start_time)

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

            # ✅ Proper time comparison
            # print("DEBUG -->", datetime.datetime.now(),  begin_time, end_time)
            if datetime.datetime.now() < end_time:
                rem += 1
                msg += f"\n• {subject}\n  {class_type}\n   🕒 {time_str}\n  ⏳{duration} Periods({duration*routine['class_time']} mins)\n"
             
        if rem == 0:
            msg += f"\n🎉 Classes finished for today → {weekday}."

        await update.message.reply_text(msg)


async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    routine = load_routine()
    weekday = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%A")
    classes = routine.get(weekday, [])
    tomo = datetime.date.today() + datetime.timedelta(days=1)

    if not classes:
        await update.message.reply_text(f"🎉 No classes for tomorrow -->{weekday}.\nEnjoy your holiday 🎉")
    else:
        start_time = datetime.datetime.combine(tomo, datetime.datetime.strptime(classes.get("start_time", "10:15:00"), '%H:%M:%S').time())  
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
    weekday = datetime.datetime.now().strftime("%A")
    today = (datetime.date.today())
    classes = routine.get(weekday, [])
    print("DEBUG -->", today)

    if not classes:
        await update.message.reply_text("🎉 No classes for today.")
        await tomorrow(update, context)
        return
    
    start_time = datetime.datetime.combine(today, datetime.datetime.strptime(classes.get("start_time", "10:15:00"), '%H:%M:%S').time())
    for sub, kind, duration in classes['classes']:
        subject = routine.get(sub, sub)
        begin_time = start_time
        end_time = begin_time + datetime.timedelta(minutes=duration * routine['class_time'])
        time_str = f"{begin_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
        start_time = end_time
        if (datetime.datetime.now()>= begin_time) and (datetime.datetime.now() <= end_time):
            class_type = f"{routine.get(kind[0], kind[0])} "
            for k in range(1, len(kind)):
                class_type += f"+ {routine.get(kind[k], kind[k])} "
            msg = f"📚 Ongoing Class:\n\n• {subject}\n  {class_type}\n  🕒{time_str}\n  ⏳{((end_time-datetime.datetime.now()).total_seconds()//60)})\n"
            await update.message.reply_text(msg)
            return

    if datetime.datetime.now() > start_time:
        await update.message.reply_text(f"🎉 Classes Finished for Today -->{weekday}.")
        await tomorrow(update, context)
        return
    
    await update.message.reply_text(f"🎉 No ongoing classes your next class starts at {start_time.strftime('%H:%M')}.")
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
# Main function to run the bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("next", upcoming))
    app.add_handler(CommandHandler("tomorrow", tomorrow))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ongoing", ongoing))
    print("✅ Bot running. Send /today in chat.\n  📌 *Available Commands:*\n\n"
        "/today - Show today's classes\n"
        "/tomorrow - Show tomorrow's classes\n"
        "/next - Show next class for today\n"
        "/ongoing - Show ongoing class\n"
        "/help - Show this help message")
    
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
