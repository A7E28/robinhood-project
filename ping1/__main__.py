
from telegram.ext import ApplicationBuilder, CommandHandler
from ping1.modules.hello import bot_start
from ping1.modules.subcal import subnet
from ping1.modules.help import help
from ping1.modules.systemstatus import bot_status, system_status, speedtest, ping, reboot
from ping1.modules.comm_checker import enable_command, disable_command
from ping1.modules.player import play_audio


from ping1 import token, LOGGER

def main() -> None:
    application = ApplicationBuilder().token(token).build()
    
    
    
    # Register commands
    application.add_handler(CommandHandler('start', bot_start))
    application.add_handler(CommandHandler('subnet', subnet))
    application.add_handler(CommandHandler('help', help))
    application.add_handler(CommandHandler('status', bot_status))
    application.add_handler(CommandHandler('sysinfo', system_status))
    application.add_handler(CommandHandler('speedtest', speedtest))
    application.add_handler(CommandHandler('ping', ping))
    application.add_handler(CommandHandler('reboot', reboot))
    application.add_handler(CommandHandler('enable', enable_command))  # Add enable command handler
    application.add_handler(CommandHandler('disable', disable_command))  # Add disable command handler
    application.add_handler(CommandHandler('music', play_audio))

  

    # Run the bot
    LOGGER.info("\nBOT started..")
    application.run_polling()

       

if __name__ == '__main__':
    main()
