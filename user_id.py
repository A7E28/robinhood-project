import json
from telethon import events, utils

# Define the dictionary to store user groups
user_groups = {
    "admin": [],
    "user": [],
}

# Function to convert a username to a user ID
async def get_user_id_by_username(client, username):
    try:
        entity = await client.get_entity(username)
        return entity.id
    except ValueError:
        return None

# Define functions to handle /add_user and /remove_user commands
async def add_user(user_id, group_name, client):
    if group_name in user_groups:
        if user_id not in user_groups[group_name]:
            user_groups[group_name].append(user_id)
            return True
    return False

def remove_user(user_id, group_name):
    if group_name in user_groups and user_id in user_groups[group_name]:
        user_groups[group_name].remove(user_id)
        return True
    return False

# Function to save user group data to user_id.json file
def save_user_groups():
    with open("user_id.json", "w") as file:
        json.dump(user_groups, file)

# Function to load user group data from user_id.json file
def load_user_groups():
    try:
        with open("user_id.json", "r") as file:
            data = json.load(file)
            if isinstance(data, dict):
                user_groups.clear()
                user_groups.update(data)
    except FileNotFoundError:
        pass

# Function to register the /add_user and /remove_user commands with the client
def register_user_id_feature(client):
    @client.on(events.NewMessage(pattern='/add_user (.+?) @(.+?)$'))
    async def add_user_handler(event):
        user_id = event.sender_id
        group_name, username = event.pattern_match.group(1).lower(), event.pattern_match.group(2).lower()
        user_id = await get_user_id_by_username(client, f'@{username}')

        if user_id and await add_user(user_id, group_name, client):
            save_user_groups()
            await event.respond(f"Added user {username} to group {group_name}")
        else:
            await event.respond("Invalid group name or username not found.")

    @client.on(events.NewMessage(pattern='/remove_user (.+?) @(.+?)$'))
    async def remove_user_handler(event):
        user_id = event.sender_id
        group_name, username = event.pattern_match.group(1).lower(), event.pattern_match.group(2).lower()
        user_id = await get_user_id_by_username(client, f'@{username}')

        if user_id and remove_user(user_id, group_name):
            save_user_groups()
            await event.respond(f"Removed user {username} from group {group_name}")
        else:
            await event.respond("Invalid group name or username not found.")

# Load user group data when the bot starts
load_user_groups()
