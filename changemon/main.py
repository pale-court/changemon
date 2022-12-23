import gevent.monkey
gevent.monkey.patch_all()

import asyncio
import asyncio_gevent

import logging
import json
from pathlib import Path
from pydantic import BaseSettings
import sys
import time
import websockets

from steam.client import SteamClient
from steam.enums.emsg import EMsg

logging.basicConfig(format="%(asctime)s | %(message)s", level=logging.INFO)
LOG = logging.getLogger()

class Settings(BaseSettings):
    appinfo_dir: Path
    steam_user: str
    steam_password: str
    steam_id_base: int
    web_pipes_url: str

asyncio.set_event_loop_policy(asyncio_gevent.EventLoopPolicy())

settings = Settings()

client = SteamClient()

@client.on("connected")
def handle_connected():
    LOG.info("Connected to %s", client.current_server_addr)

@client.on("reconnect")
def handle_reconnect(delay):
    LOG.info("Reconnect in %ds...", delay)

@client.on("disconnected")
def handle_disconnect():
    LOG.info("Disconnected.")

    if client.relogin_available:
        LOG.info("Reconnecting...")
        client.reconnect(maxdelay=30)
        client.relogin()

client.login(settings.steam_user, settings.steam_password, login_id=settings.steam_id_base + 12)

POE_APP_ID = 238960

missed_dir = settings.appinfo_dir / 'missed'
saved_dir = settings.appinfo_dir / 'saved'

missed_dir.mkdir(parents=True, exist_ok=True)
saved_dir.mkdir(parents=True, exist_ok=True)

def save_appinfo(appinfo):
    path = saved_dir / f'appinfo-{appinfo["appid"]}-{appinfo["_change_number"]}.json'
    if not path.exists():
        with path.open('w') as fh:
            out_js = {
                "write_time": int(time.time()),
                "appinfo": appinfo,
            }
            json.dump(out_js, fh, indent=4)


def fetch(appids, notify_changeid = None):
    infos = client.get_product_info(apps=[POE_APP_ID], timeout=30)
    if infos and "apps" in infos:
        apps = infos["apps"]
        for appid, appinfo in apps.items():
            changenumber = appinfo["_change_number"]
            if notify_changeid is not None:
                if changenumber > notify_changeid:
                    print(
                        f'missed changenumber {notify_changeid}, got {changenumber}')
                    save_appinfo(appinfo)
                elif changenumber < notify_changeid:
                    print(
                        f'expected changenumber {notify_changeid}, got {changenumber}')
            else:
                save_appinfo(appinfo)

async def listener():
    async for websocket in websockets.connect(settings.web_pipes_url, subprotocols=['steam-pics']):
        print('Connected to WebPipes.')
        try:
            async for message in websocket:
                msg = json.loads(message)
                if msg["Type"] != "Changelist":
                    continue
                notify_changeid = msg["ChangeNumber"]
                appids = list(map(int, msg["Apps"].keys()))
                if len(appids) == 0:
                    continue
                if POE_APP_ID in appids:
                    fetch([POE_APP_ID])

        except websockets.ConnectionClosed:
            print('Disconnected from WebPipes.')
            # continue

def main():
    fetch([POE_APP_ID])
    asyncio.run(listener())