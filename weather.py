import requests
import json
from telethon import events
from credentials import API_KEY, API_URL

def get_user_location(user_id):
    try:
        with open('user_locations.json', 'r') as f:
            user_locations = json.load(f)
            return user_locations.get(str(user_id))
    except FileNotFoundError:
        return None

def get_weather(city_name):
    params = {'q': city_name, 'appid': API_KEY, 'units': 'metric'}
    response = requests.get(API_URL, params=params)
    data = response.json()
    return data

def register_weather_feature(client):
    @client.on(events.NewMessage(pattern='/weather'))
    async def weather(event):
        user_id = event.sender_id
        saved_location = get_user_location(user_id)

        if saved_location:
            weather_data = get_weather(saved_location)
            if weather_data.get('main'):
                temp = weather_data['main']['temp']
                description = weather_data['weather'][0]['description']
                response_text = f"The weather in {saved_location} is {description} with a temperature of {temp}°C."
            else:
                response_text = f"Sorry, I couldn't fetch weather information for {saved_location}."
        else:
            response_text = "Please set your preferred location using /setlocation command."
        
        await event.respond(response_text)
        raise events.StopPropagation
