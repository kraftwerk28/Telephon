from aiohttp import ClientTimeout
import asyncio
from dotenv import load_dotenv
import logging as log
import os
import sys
import subprocess
from telethon import tl
from wand.image import Image

from core import *
from core.utils import *
import utils

load_dotenv()

log.basicConfig(
    format='[%(asctime)s] %(message)s',
    datefmt='%d.%m.%Y %H:%M:%S',
    level=log.INFO
)

config = InitConfig(
    os.path.abspath('./.sessions/tgai28'),
    os.getenv('API_ID'),
    os.getenv('API_HASH')
)

VOICE_API_URL = os.getenv('VOICE_API_URL')
app = TgAI(config)


@app.on_command('help', named_args=['object', 'sample'], direction=MsgDir.OUT)
async def help(ctx: TgAIContext):
    await ctx.msg.reply(
        'Help: {}, {}'.format(
            ctx.named_args['object'],
            ctx.named_args['sample'],
        )
    )


@app.on_command('tagall', direction=MsgDir.OUT)
async def tagall(ctx: TgAIContext):
    users = await ctx.client.get_participants(ctx.msg.chat_id)
    if len(users) > 50:
        return
    mentions = [utils.mention(u) for u in users if not u.bot and not u.is_self]
    if mentions:
        sent = await ctx.msg.respond(' '.join(mentions))
        ctx.state.autorm[ctx.msg.id] = (sent.chat_id, sent.id)


@app.on_delete()
async def on_delete(ctx: TgAIContext):
    autorm = ctx.state.autorm
    stickerids = [i for i in ctx.event.deleted_ids if i in autorm]
    for id in stickerids:
        chat_id, msg_id = autorm[id]
        try:
            await ctx.client.delete_messages(chat_id, msg_id)
        except:
            pass
        autorm.pop(id)


@app.on_command('id', argcount=1)
async def id(ctx: TgAIContext):
    msg, client = ctx.msg, ctx.client

    if msg.out:
        await msg.delete()

    reply = await msg.get_reply_message()
    text = ''
    chat = msg.chat
    if msg.is_group:
        text = f'<b>Group chat</b>: {chat.title} [<code>{chat.id}</code>]\n'
    elif msg.is_private:
        text = (
            f'<b>Private chat</b>: {utils.mention(chat)} ' +
            f'[<code>{chat.id}</code>]\n'
        )

    if reply is not None:
        sender: tl.types.User = reply.sender
        text += '<b>Reply:</b>\n'
        text += (
            f'  <b>User</b>: {utils.mention(sender)} ' +
            f'[<code>{sender.id}</code>]\n'
        )
        text += f'  <b>Message</b>: [<code>{reply.id}</code>]\n'
        # If message has any resource:
        if reply.sticker is not None:
            text += utils.repr_document('Sticker', reply.sticker)
        if reply.gif is not None:
            text += utils.repr_document('GIF', reply.gif)
        if reply.photo is not None:
            text += utils.repr_photo('Photo', reply.photo)

    if not msg.out:
        sent = await msg.reply(text, parse_mode='html')
        ctx.state.autorm[ctx.msg.id] = (sent.chat_id, sent.id)
    elif ctx.args[0] == 'here':
        await msg.respond(text, parse_mode='html')
    else:
        await client.send_message('me', text, parse_mode='html')


async def flip_sticker(ctx: TgAIContext, msg: tl.custom.message.Message):
    temp_path = 'tl.webp'
    await msg.download_media(file=temp_path)

    img = Image(filename=temp_path)
    img.flop()
    img.save(filename=temp_path)

    sent: tl.custom.Message = await msg.reply(file=temp_path)
    ctx.state.autorm[msg.id] = (sent.chat_id, sent.id)
    os.remove(temp_path)


@app.on_command('flip', direction=MsgDir.OUT)
async def flip(ctx: TgAIContext):
    msg = ctx.msg
    target: tl.custom.Message = await msg.get_reply_message()
    if (target and target.sticker):
        target.sticker
        await msg.delete()
        await flip_sticker(ctx, target)


@app.on_command(['say', 'гл'], direction=MsgDir.OUT, argcount=-1)
async def say(ctx: TgAIContext):
    msg, client, http_client = ctx.msg, ctx.client, ctx.http_client

    if msg.out:
        await msg.delete()

    voice, *words = ctx.args
    VOICE_MATCH = utils.VOICE_MATCH
    if voice in VOICE_MATCH:
        phrase = ' '.join(words)
        voice = VOICE_MATCH[voice]
    else:
        phrase = ' '.join([voice, *words])
        voice = 'maxim'
    input_name, temp_name = 'temp__.wav', 'temp__.ogg'

    data = {'phrase': phrase, 'voice': voice}
    try:
        resp = await http_client.post(
            '{}/say'.format(VOICE_API_URL),
            json=data,
            timeout=ClientTimeout(total=5)
        )
    except asyncio.TimeoutError as e:
        await client.send_message(
            'me',
            'Timeout making voice API request.'
        )
        return
    open(input_name, 'wb').write(await resp.read())

    subprocess.run(
        f'ffmpeg -i {input_name} -acodec libopus {temp_name} -y'.split(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    sent = await client.send_file(
        msg.chat_id,
        temp_name,
        voice_note=True,
        reply_to=msg.reply_to_msg_id if msg.out else msg.id
    )

    if not msg.out:
        ctx.state.autorm[ctx.msg.id] = (sent.chat_id, sent.id)

    os.unlink(temp_name)
    os.unlink(input_name)


@app.on_command(['фр', 'fr'], direction=MsgDir.OUT, argcount=-1)
async def framed(ctx: TgAIContext):
    msg, client, state = ctx.msg, ctx.client, ctx.state
    if msg.entities:
        return
    framed = utils.bordered(' '.join(ctx.args), fr_type='double')
    await msg.delete()
    await client.send_message(
        msg.chat_id,
        framed,
        parse_mode='HTML',
        link_preview='false',
        reply_to=msg.reply_to_msg_id
    )


if __name__ == '__main__':
    sys.exit(app.start())
