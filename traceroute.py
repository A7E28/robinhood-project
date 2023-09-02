import telebot
import subprocess
import platform
import time
from datetime import datetime  # Import the datetime module

def register_traceroute_feature(bot):
    @bot.message_handler(commands=['traceroute'])
    def traceroute(message):
        # Split the message text to extract the host
        command_args = message.text.split()[1:]
        
        if not command_args:
            bot.reply_to(message, "Please provide a host to traceroute. Usage: /traceroute <host>")
            return
        
        host = command_args[0]
        last_sent_message_id = None

        try:
            # Determine the OS platform
            os_platform = platform.system()

            # Define the traceroute command based on the OS platform
            if os_platform == 'Windows':
                traceroute_cmd = ['tracert', host]
            elif os_platform == 'Linux':
                traceroute_cmd = ['traceroute', host]
            else:
                bot.reply_to(message, "Unsupported operating system.")
                return

            # Execute the traceroute command and capture the output
            traceroute_process = subprocess.Popen(traceroute_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)
            
            # Initialize the traceroute output text
            traceroute_output = f"Traceroute results for {host}:\n```\n"

            # Process and send updates for each hop
            for line in traceroute_process.stdout:
                line = line.strip()  # Remove leading/trailing whitespace

                # Append each line of the traceroute output to the existing text
                traceroute_output += f"{line}\n"

                # Get the current timestamp in a human-readable format
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                edited_text = f"{traceroute_output}```\nUpdated at {timestamp}"

                # Check if there are changes to the message content
                if edited_text != traceroute_output:
                    if last_sent_message_id:
                        # Edit the last sent message to update the traceroute output with the formatted timestamp
                        bot.edit_message_text(edited_text, message.chat.id, last_sent_message_id, parse_mode="Markdown")
                    else:
                        # Send a new message if last_sent_message_id is not set
                        last_sent_message = bot.send_message(message.chat.id, edited_text, parse_mode="Markdown")
                        last_sent_message_id = last_sent_message.message_id
                else:
                    # Add a slight delay before sending a new message with the same content
                    time.sleep(0.1)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    edited_text = f"{traceroute_output}```\nUpdated at {timestamp}"
                    last_sent_message = bot.send_message(message.chat.id, edited_text, parse_mode="Markdown")
                    last_sent_message_id = last_sent_message.message_id

            # Wait for the traceroute process to finish
            traceroute_process.wait()

            # Send the final completion message
            bot.send_message(message.chat.id, "Traceroute completed.")
        except Exception as e:
            bot.reply_to(message, f"An error occurred: {str(e)}")
