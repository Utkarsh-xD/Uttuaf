import asyncio
import logging 
import logging.config
import httpx
import sys
from database import db 
from config import Config  
from pyrogram import Client, __version__
from pyrogram.raw.all import layer 
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait 

logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

class Bot(Client): 
    def __init__(self):
        super().__init__(
            Config.BOT_SESSION,
            api_hash=Config.API_HASH,
            api_id=Config.API_ID,
            plugins={
                "root": "plugins"
            },
            workers=50,
            bot_token=Config.BOT_TOKEN
        )
        self.log = logging

    async def validate_license(self):
        if not Config.LICENSE_KEY:
            logging.error("LICENSE_KEY not set in environment!")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{Config.AUTH_SERVER_URL}/license/validate",
                    json={
                        "license_key": Config.LICENSE_KEY,
                        "bot_token": Config.BOT_TOKEN
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    logging.info(f"License is valid. Expiry: {data.get('expiry_date')}")
                    return True
                else:
                    logging.error(f"License validation failed: {response.json().get('detail')}")
                    return False
        except Exception as e:
            logging.error(f"Error connecting to auth server: {e}")
            # Failsafe: if auth server is down, we might want to allow 1 retry or a grace period
            # For now, let's be strict or implement a simple retry
            return "retry"

    async def heartbeat(self):
        while True:
            await asyncio.sleep(3 * 3600) # 3 hours
            status = await self.validate_license()
            if status is False:
                logging.error("License validation failed during heartbeat. Shutting down...")
                # Exit the process
                sys.exit(1)
            elif status == "retry":
                logging.warning("Auth server unreachable during heartbeat, will retry in 1 hour.")
                await asyncio.sleep(3600)

    async def start(self):
        # License check on startup
        license_status = await self.validate_license()
        if license_status is False:
            logging.error("License validation failed on startup. Bot will not start.")
            sys.exit(1)
        
        await super().start()
        # Start heartbeat
        asyncio.create_task(self.heartbeat())
        
        me = await self.get_me()
        logging.info(f"{me.first_name} with for pyrogram v{__version__} (Layer {layer}) started on @{me.username}.")
        self.id = me.id
        self.username = me.username
        self.first_name = me.first_name
        self.set_parse_mode(ParseMode.DEFAULT)
        text = "**๏[-ิ_•ิ]๏ bot restarted !**"
        logging.info(text)

        # Check if database URI is default broken one
        if "mongodb+srv://chhjgjkkjhkjhkjh@cluster0.xowzpr4.mongodb.net/" in Config.DATABASE_URI:
             logging.error("You have not set the DATABASE environment variable. The bot will not function correctly.")
             return

        try:
            success = failed = 0
            users = await db.get_all_frwd()
            async for user in users:
               chat_id = user['user_id']
               try:
                  await self.send_message(chat_id, text)
                  success += 1
               except FloodWait as e:
                  await asyncio.sleep(e.value + 1)
                  await self.send_message(chat_id, text)
                  success += 1
               except Exception:
                  failed += 1

            if (success + failed) != 0:
               await db.rmve_frwd(all=True)
               logging.info(f"Restart message status"
                     f"success: {success}"
                     f"failed: {failed}")
        except Exception as e:
            logging.error(f"Failed to send restart messages or connect to DB: {e}")

    async def stop(self, *args):
        msg = f"@{self.username} stopped. Bye."
        await super().stop()
        logging.info(msg)
