from telethon import events
import json

def save_location(user_id, location):
    try:
        with open('user_locations.json', 'r') as f:
            user_locations = json.load(f)
    except FileNotFoundError:
        user_locations = {}

    user_locations[str(user_id)] = location

    with open('user_locations.json', 'w') as f:
        json.dump(user_locations, f)

def register_location_feature(client):
    @client.on(events.NewMessage(pattern='/setlocation'))
    async def set_location(event):
        user_id = event.sender_id
        location = event.raw_text[13:].strip()  # Extract text after '/setlocation' command

        save_location(user_id, location)

        await event.respond(f"Your preferred location has been set to {location}.")
        raise events.StopPropagation
