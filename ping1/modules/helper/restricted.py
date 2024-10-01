import asyncio

from telegram import Update
from telegram.ext import CallbackContext


BossID = [] #add your owner chat id here

def boss(func):
    '''
    This decorator fucntion will restrict any fucntion to the provided user_id
    only. Usally it should set to the developer user_id.

    '''
    async def wrapper(update: Update, context: CallbackContext) -> None:
        if update.message and update.message.from_user.id not in BossID:
            return
        asyncio.create_task(func(update, context))
    return wrapper

