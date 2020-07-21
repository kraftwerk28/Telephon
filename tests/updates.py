#!/usr/bin/env python
import os
import re
import sys
import json
from telethon import TelegramClient, events
from dotenv import load_dotenv
from init_client import make_client
from pprint import pprint
import asyncio
from aiohttp import (ClientSession, ClientTimeout)

# client: TelegramClient


def on_new_update(e):
    # if 'status' in e:
    #     return
    pprint(vars(e))


async def main():
    client = ClientSession()
    url = 'http://51.89.121.93:8080/say'
    headers = {
        'content-type': 'application/json'
    }
    try:
        res = await client.post(
            url,
            headers=headers,
            json={'phrase': 'привет, мир'},
            timeout=ClientTimeout(total=5),
        )
    except asyncio.TimeoutError as e:
        print('Timeout error', e)
        await client.close()
        sys.exit(1)
    print(res.status)
    with open('say.wav', 'wb+') as file:
        file.write(res.content)
    await client.close()
    # await client.start()
    # sent = await client.send_file(
    #     'me',
    #     '/home/kraftwerk28/Music/astronomia.ogg',
    #     voice_note=True,
    # )

    # client.add_event_handler(
    #     on_new_update,
    #     event=events.UserUpdate
    # )
    # msgs = await client.get_messages('profunctor_io', 2)
    # print(str(msgs[-1]))
    # btns = msgs[-1].buttons
    # pprint(btns)
    # click_result = await btns[0][0].click()
    # print('click result', click_result)

    # await client.disconnect()
    # await client.run_until_disconnected()


if __name__ == '__main__':
    load_dotenv()

    VOICE_API_URL = os.getenv('VOICEAPI_URL')
    loop = asyncio.get_event_loop()
    # client = make_client()
    # loop = client.loop
    loop.run_until_complete(main())
    loop.close()
