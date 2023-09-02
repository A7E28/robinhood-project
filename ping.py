import subprocess
import time
from datetime import datetime
import platform

def register_ping_feature(bot):
    @bot.message_handler(commands=['ping'])
    def ping(message):
        # Split the message text to extract the host and packet count arguments
        command_args = message.text.split()[1:]

        if not command_args:
            bot.reply_to(message, "Please provide a host to ping. Usage: /ping <host> [packet_count]")
            return

        host = command_args[0]
        packet_count = int(command_args[1]) if len(command_args) > 1 else 4  # Default to 4 packets

        try:
            if platform.system().lower() == "windows":
                # On Windows, use the 'ping' command with the /n flag for packet count
                ping_process = subprocess.Popen(['ping', host, '-n', str(packet_count)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)
            else:
                # On Unix-like systems (Linux/macOS), use the 'ping' command with the -c flag for packet count
                ping_process = subprocess.Popen(['ping', '-c', str(packet_count), host], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)

            # Send an initial message
            initial_message = bot.reply_to(message, f"Pinging {host} with {packet_count} packets...")

            # Initialize the ping output text
            ping_output = f"Ping results for {host} (Packet count: {packet_count}):\n```\n"

            # Process and send updates for each packet
            received_packets = 0
            total_packets = 0
            lost_packets = 0
            for line in ping_process.stdout:
                line = line.strip()  # Remove leading/trailing whitespace

                # Append each line of the ping output to the existing text
                ping_output += f"{line}\n"

                # Check for received and lost packets on Windows
                if "Packets: Sent" in line:
                    parts = line.split(',')
                    sent = int(parts[0].split('=')[1].strip())
                    received = int(parts[1].split('=')[1].strip())
                    lost_packets = sent - received
                    received_packets = received
                    total_packets = sent

                # Check for received packets on Linux
                if "icmp_seq" in line and "time=" in line:
                    received_packets += 1

                # Add a human-readable timestamp to the message text
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                edited_text = f"{ping_output}```\nUpdated at {timestamp}"

                # Edit the initial message to update the ping output with the timestamp
                bot.edit_message_text(edited_text, message.chat.id, initial_message.message_id, parse_mode="Markdown")

                # Sleep for 1 second to mimic packet delay
                time.sleep(1)

            # Wait for the ping process to finish
            ping_process.wait()

            # Determine the completion message based on packet loss and ping times
            if received_packets == 0:
                completion_message = f"Ping to {host} completed. All {total_packets} packets lost, host unreachable."
            else:
                completion_message = f"Ping to {host} completed. Sent {total_packets} packets, {lost_packets} packets lost."

            # Send the final completion message
            bot.edit_message_text(f"{ping_output}```\n{completion_message}", message.chat.id, initial_message.message_id, parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"An error occurred: {str(e)}")
