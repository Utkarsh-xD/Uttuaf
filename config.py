from os import environ 

class Config:
    API_ID = environ.get("API_ID", "12916125")
    API_HASH = environ.get("API_HASH", "dfebf9cc52b859771cf8a1d447e751a5")
    BOT_TOKEN = environ.get("BOT_TOKEN", "2073340158:AAEd_8yntof1ctSZUHptuDLi6oJtSMmkNPI") 
    BOT_SESSION = environ.get("BOT_SESSION", "bot") 
    DATABASE_URI = environ.get("DATABASE", "mongodb+srv://minakshisharma12320:FFEeUVJyHJKFJKa1@cluster0.0ofreqe.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    DATABASE_NAME = environ.get("DATABASE_NAME", "forward-bot")
    BOT_OWNER_ID = [int(id) for id in environ.get("BOT_OWNER_ID", '1651746145').split()]

class temp(object): 
    lock = {}
    CANCEL = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []
    
