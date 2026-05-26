from os import environ 

class Config:
    API_ID = environ.get("API_ID", "17503698")
    API_HASH = environ.get("API_HASH", "d16ee3a0592e081e683be2c2e8bb93a7")
    BOT_TOKEN = environ.get("BOT_TOKEN", "6889564069:AAFdH1rBTqo31Nao_CSCI2LZEi76YqH9rn8") 
    BOT_SESSION = environ.get("BOT_SESSION", "bot") 
    DATABASE_URI = environ.get("DATABASE", "mongodb+srv://utkarsh:utkarsh@filetolinkbot.cpc2u3e.mongodb.net/?appName=filetolinkbot")
    DATABASE_NAME = environ.get("DATABASE_NAME", "forward-bot")
    BOT_OWNER_ID = [int(id) for id in environ.get("BOT_OWNER_ID", '1245831019').split()]

class temp(object): 
    lock = {}
    CANCEL = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []

