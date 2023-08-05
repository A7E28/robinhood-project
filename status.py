import ping3
from telethon import events

def get_response_time(device_line):
    try:
        device_name, ip = device_line.strip().split(', ')
        response_time = ping3.ping(ip, timeout=2, unit='ms')
        if response_time is not None:
            return f"{device_name} ({ip}): {response_time:.2f} ms", True
        else:
            return f"{device_name} ({ip}): Offline", False

    except ping3.PingError as e:
        print("Ping error:", e)
        return f"{device_name} ({ip}): Host unreachable or invalid IP", False

    except ping3.Timeout as e:
        print("Ping timeout:", e)
        return f"{device_name} ({ip}): Request timed out", False

def register_status_feature(client):
    @client.on(events.NewMessage(pattern='/status'))
    async def check_status(event):
        with open('device.txt', 'r') as file:
            device_lines = file.readlines()

        online_msg = "Online Devices:\n"
        offline_msg = ""

        for line in device_lines:
            print(f"Pinging device: {line.strip()}")
            response_time, is_online = get_response_time(line)

            if is_online:
                online_msg += f"{response_time}\n"
            else:
                offline_msg += f"{response_time}\n"

        response_msg = online_msg
        if offline_msg:
            response_msg += "\nOffline Devices:\n" + offline_msg

        print("Response message:", response_msg)
        await event.respond(response_msg)
        raise events.StopPropagation
