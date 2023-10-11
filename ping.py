from telethon import events
import asyncio
import platform
from ping3 import ping

def register_ping_feature(client):
    @client.on(events.NewMessage(pattern='/ping'))
    async def ping_command(event):
        # Extract the user's request from the message
        args = event.text.split()
        host = None
        ping_count = 4  # Default ping count

        # Process command arguments
        if len(args) > 1:
            host = args[1]
            for i in range(2, len(args)):
                if args[i] == '-t' and i + 1 < len(args):
                    try:
                        ping_count = int(args[i + 1])
                        if ping_count < 1:
                            await event.respond("Invalid ping count. Please specify a positive integer.")
                            return
                    except ValueError:
                        await event.respond("Invalid ping count. Please specify a positive integer.")
                        return

        # Check if the user provided a host
        if not host:
            await event.respond("Please provide a host (IP address or domain) to ping.")
            return

        try:
            response = f'Pinging {host}...\n'
            message = await event.respond(f'```{response}```', parse_mode='markdown')

            for _ in range(ping_count):
                result = ping(host)
                if result is not None:
                    response += f"Reply from {host}: time={result*1000:.0f}ms\n"
                message = await message.edit(f'```{response}```', parse_mode='markdown')
                await asyncio.sleep(0.1)

            # Calculate statistics
            results = [ping(host) for _ in range(ping_count)]
            if all(result is not None for result in results):
                response += "Ping statistics:\n"
                response += f"Packets: Sent = {ping_count}, Received = {len(results)}, Lost = {ping_count - len(results)} " \
                            f"({((ping_count - len(results)) / ping_count) * 100:.2f}% loss)\n"
                response += "Approximate round trip times in milliseconds:\n"
                response += f"Minimum = {min(results)*1000:.0f}ms, Maximum = {max(results)*1000:.0f}ms, " \
                            f"Average = {(sum(results) / len(results)*1000):.2f}ms"

            # Send the final response
            await message.edit(f'```{response}```', parse_mode='markdown')

        except Exception as e:
            await event.respond(f"Error executing ping: {str(e)}")
