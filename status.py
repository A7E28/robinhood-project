import ping3
from telethon import events
import re

def get_response_time(ip):
    try:
        response_time = ping3.ping(ip, timeout=2, unit='ms')
        if response_time is not None:
            return f"{ip}: {response_time:.2f} ms", True
        else:
            return f"{ip}: Offline", False

    except Exception as e:
        print("Ping error:", e)
        return f"{ip}: Host unreachable or invalid IP", False

def get_device_name_and_ip(identifier):
    with open('device.txt', 'r') as file:
        device_lines = file.readlines()

    for line in device_lines:
        name, ip = line.strip().split(', ')
        if identifier == name or identifier == ip:
            return name, ip

    return None, None

def register_status_feature(client):
    @client.on(events.NewMessage(pattern='/status_device'))
    async def check_specific_status(event):
        identifier = event.raw_text.split(maxsplit=1)[1]  # Extract the device name or IP from the message

        device, ip = get_device_name_and_ip(identifier)

        if device is not None and ip is not None:
            response_time, is_online = get_response_time(ip)

            if is_online:
                response_msg = f"{device} is online: {response_time}"
            else:
                response_msg = f"{device}is offline"
        else:
            response_msg = f"Device {identifier} not found in the list."

        await event.respond(response_msg)

    @client.on(events.NewMessage(pattern='/all_status'))
    async def check_all_status(event):
        with open('device.txt', 'r') as file:
            device_lines = file.readlines()

        online_msg = "Online Devices:\n"
        offline_msg = ""

        for line in device_lines:
            name, ip = line.strip().split(', ')
            response_time, is_online = get_response_time(ip)

            if is_online:
                online_msg += f"{name} ({ip}): {response_time}\n"
            else:
                offline_msg += f"{name} ({ip}): Offline\n"

        response_msg = online_msg
        if offline_msg:
            response_msg += "\nOffline Devices:\n" + offline_msg

        await event.respond(response_msg)
