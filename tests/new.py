import os
import sys
import logging as log
from dotenv import load_dotenv
import asyncio
import aiohttp
import subprocess

from Telephon.core import *
from Telephon.core.utils import *
from telethon import tl

if os.getenv('PYTHON_ENV') != 'production':
    load_dotenv()
    # Otherwise .env is loaded by docker

log.basicConfig(
    format='[%(asctime)s] %(message)s',
    datefmt='%d.%m.%Y %H:%M:%S',
    level=log.INFO
)

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION_PATH = os.path.abspath('./.sessions/tgai28')
VOICE_API_URL = os.getenv('VOICE_API_URL')
config = InitConfig(SESSION_PATH, API_ID, API_HASH)
app = Telephon(config)


def mention(user: tl.types.User, with_link=False):
    if user.username:
        return f'@{user.username}'
    name = user.first_name
    if user.last_name:
        name += ' ' + user.last_name
    if with_link:
        return f'<a href="tg://user?id={user.id}">{name}</a>'
    return name


@app.on_command('help', named_args=['object', 'sample'])
async def help(ctx: Context):
    await ctx.reply(f'Named args: {str(ctx.named_args)}',
                    reply=True,
                    delete_command_message=True)


@app.on_command('tagall')
async def tagall(ctx: Context):
    users = await ctx.client.get_participants(ctx.msg.chat_id)
    if len(users) > 50:
        return
    mentions = [mention(u) for u in users if not u.bot and not u.is_self]
    print(mentions)
    if mentions:
        await ctx.reply(' '.join(mentions), reply=True)
        # sent = await ctx.msg.respond(' '.join(mentions))
        # ctx.state.autorm[ctx.msg.id] = (sent.chat_id, sent.id)


@app.on_command(['say', 'гл'])
async def voice_engine(ctx: Context):
    msg, client, http_client = ctx.msg, ctx.client, ctx.http_client

    await ctx.reply(delete_command_message=True)
    voices = 'maxim nikolai'.split()

    voice = None
    if len(ctx.args) > 0 and ctx.args[0] in voices:
        voice, *rest = ctx.args
    else:
        rest = ctx.args
    phrase = ' '.join(rest)
    # voicestr = '|'.join(voices)
    # voice, phrase = re.search(
    #     fr'({voicestr})?\s*(.+)',
    #     text,
    #     re.DOTALL
    # ).groups()

    input_name, temp_name = 'temp__.wav', 'temp__.ogg'

    req_body = {'phrase': phrase, 'voice': voice or 'nikolai'}
    try:
        resp = await http_client.post(
            f'{VOICE_API_URL}/say',
            json=req_body,
            timeout=aiohttp.ClientTimeout(total=5)
        )
    except asyncio.TimeoutError as e:
        await ctx.reply('Timeout making voice API request.',
                        send_to_saves=True)
        return

    with await open(input_name, 'wb') as f:
        f.write(await resp.read())

    subprocess.run(
        # In this case .split() is safe because there are no quoted arguments apriori.
        f'ffmpeg -i {input_name} -acodec libopus {temp_name} -y'.split(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    sent = await client.send_file(
        msg.chat_id,
        temp_name,
        voice_note=True,
        reply_to=msg.reply_to_msg_id if msg.out else msg.id
    )

    os.unlink(temp_name)
    os.unlink(input_name)


# @app.on_delete()
# async def on_delete(ctx: Context):
#     autorm = ctx.state.autorm
#     stickerids = [i for i in ctx.event.deleted_ids if i in autorm]
#     for _id in stickerids:
#         chat_id, msg_id = autorm[_id]
#         try:
#             await ctx.client.delete_messages(chat_id, msg_id)
#         except:
#             pass
#         del autorm[_id]


@app.on_command('id', named_args=['here'])
async def id(ctx: Context):
    msg = ctx.msg

    reply = await msg.get_reply_message()
    text = ''
    chat = msg.chat
    if msg.is_group:
        text = f'<b>Chat</b>: {chat.title} [<code>{chat.id}</code>]\n'
    elif msg.is_private:
        text = (
            f'<b>Private chat</b>: {mention(chat)} ' +
            f'[<code>{chat.id}</code>]\n'
        )

    if reply is not None:
        sender: tl.types.User = reply.sender
        text += (
            f'<b>User</b>: {mention(sender)} ' +
            f'[<code>{sender.id}</code>]\n'
        )
        text += f'<b>Message</b>: [<code>{reply.id}</code>]\n'
        # If message has any resource:
        # if reply.sticker is not None:
        #     text += utils.repr_document('Sticker', reply.sticker)
        # if reply.gif is not None:
        #     text += utils.repr_document('GIF', reply.gif)
        # if reply.photo is not None:
        #     text += utils.repr_photo('Photo', reply.photo)

    await ctx.reply(text,
                    send_to_saves=ctx.named_args['here'] != 'here',
                    delete_command_message=True)


if __name__ == '__main__':
    app.start()
