from telegram import Update
from telegram.ext import ContextTypes
import psutil
import time
import speedtest as speedtest_lib  # Renamed the imported speedtest library
import subprocess
import os
import sys
from ping1.modules.comm_checker import command_states

# Global variable to keep track of bot start time
bot_start_time = time.time()

async def bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Calculate uptime
        uptime = time.time() - bot_start_time
        uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime))
        
        # Prepare response message
        response = (
            f"Bot Status: Running\n"
            f"Uptime: {uptime_str}\n"
        )

        await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    except Exception as e:
        print(f"Error in bot_status: {e}")

async def system_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Get system information
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        swap_info = psutil.swap_memory()
        disk_info = psutil.disk_usage('/')
        
        # Prepare response message
        response = (
            f"**System Status**\n"
            f"🖥️ **CPU Usage:** {cpu_usage}%\n"
            f"🧠 **Memory Usage:** {memory_info.percent}% "
            f"({memory_info.used / (1024 ** 2):.2f} MB used of {memory_info.total / (1024 ** 2):.2f} MB)\n"
            f"🔄 **Swap Memory:** {swap_info.percent}% "
            f"({swap_info.used / (1024 ** 2):.2f} MB used of {swap_info.total / (1024 ** 2):.2f} MB)\n"
            f"💾 **Disk Usage:** {disk_info.percent}% "
            f"({disk_info.used / (1024 ** 3):.2f} GB used of {disk_info.total / (1024 ** 3):.2f} GB)\n"
        )

        # Check for battery info and append if available
        battery = psutil.sensors_battery()
        if battery:
            battery_status = f"🔋 **Battery Status:** {battery.percent}% {'🔌' if battery.power_plugged else '⚡'}\n"
            response += battery_status  # Append battery status to response

        await context.bot.send_message(chat_id=update.effective_chat.id, text=response, parse_mode='Markdown')
    except Exception as e:
        print(f"Error in system_status: {e}")


async def speedtest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not command_states['speedtest']:
        await update.message.reply_text("The speedtest command is currently disabled.")
        return

    message = await context.bot.send_message(chat_id=update.effective_chat.id, text="Finding the best server...")

    try:
        st = speedtest_lib.Speedtest()
        st.get_best_server()  # Simulate server finding

        await message.edit_text("Testing download speed...")
        download_speed = st.download() / (10**6)  # Convert to Mbps

        await message.edit_text("Testing upload speed...")
        upload_speed = st.upload() / (10**6)  # Convert to Mbps

        response = (
            f"Download Speed: {download_speed:.2f} Mbps\n"
            f"Upload Speed: {upload_speed:.2f} Mbps\n"
        )
        await message.edit_text(response)  # Edit the message with the final results

    except speedtest_lib.ConfigRetrievalError:
        await message.edit_text("Error retrieving speed test configuration. Please try again later.")
        print("ConfigRetrievalError: Unable to access speed test server configuration.")
    except Exception as e:
        await message.edit_text("Error performing speed test. Please check your connection.")
        print(f"Error in speedtest: {e}")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not command_states['ping']:
        await update.message.reply_text("The ping command is currently disabled.")
        return
    
    if len(context.args) == 0:
        await update.message.reply_text('Usage: /ping <hostname>')
        return

    hostname = context.args[0]
    message = await context.bot.send_message(chat_id=update.effective_chat.id, text="Pinging...")

    try:
        # Check the platform and set parameters accordingly
        if os.name == 'nt':  # Windows
            param = '-n'  # Windows uses -n
        else:  # Unix/Linux
            param = '-c'  # Linux uses -c
        
        result = subprocess.run(['ping', param, '4', hostname], capture_output=True, text=True)

        # Informing user about results
        if result.returncode == 0:
            await message.edit_text(f"Ping successful!\n{result.stdout}")
        else:
            await message.edit_text(f"Ping failed:\n{result.stderr}")
    except Exception as e:
        await message.edit_text("Error performing ping. Please check your hostname.")
        print(f"Error in ping: {e}")


async def reboot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not command_states['speedtest']:
        await update.message.reply_text("The speedtest command is currently disabled.")
        return    
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Rebooting bot... Please wait...")

    # Use subprocess to start a new process
    subprocess.Popen([sys.executable] + sys.argv)  # Start a new instance of the bot
    await context.bot.send_message(chat_id=update.effective_chat.id, text="The bot has been restarted successfully! 🎉")

    os._exit(0)  # Exit the current process to ensure the bot restarts cleanly

