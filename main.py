import os
import re
import sys
import json
import logging
from typing import List

import asyncio
from aiohttp import ClientSession, ClientTimeout
import subprocess
from telethon import TelegramClient, events, types, tl, Button, client
from dotenv import load_dotenv
from wand.image import Image

import utils
from init_client import make_client

PICUTRES_PATH = os.path.join(os.path.expanduser('~'), 'Pictures/')
HELP_TEXT = '''
.fr <text> - send framed text
.flip_stickers - toggle stickers flipping
.flip - flip sticker to which reply message is
.toggle_frame - toggle frame type
.toggle_dot - if do append dot to the messages
.toggle_tagall - toggle tagging
.status - display status
.help - display this message
.[st|ст] <text> - staroslav text
'''
VOICE_API_URL: str
JOKE_API_URL: str
TAG_ALL_LIMIT = 50

client: TelegramClient = None
http_client: ClientSession = None
flip_stickers = False
append_dot = False
frame_type = 'single'
stickers_map = {}
allow_tag_all = True

async def flip_sticker(msg: tl.custom.message.Message):
    global stickers_map
    temp_path = 'tl.webp'
    await msg.download_media(file=temp_path)

    img = Image(filename=temp_path)
    img.flop()
    img.save(filename=temp_path)

    sent: tl.custom.Message = await msg.reply(file=temp_path)
    stickers_map[msg.id] = (sent.chat_id, sent.id)
    os.remove(temp_path)


async def on_new_message_me(event: events.NewMessage):
    global allow_tag_all
    global flip_stickers
    global frame_type
    global append_dot

    msg: tl.custom.message.Message = event.message
    command, text = event.pattern_match.groups()

    if command == 'stop_ai':
        await msg.delete()
        await client.send_message(
            'me',
            'AI server stopped...'
        )
        await handle_exit()

    elif command == 'get_msg':
        (entity_like, cnt) = re.match(
            r'(\w+)(?:\s+)?(?:(\d+))?',
            text
        ).groups()
        cnt = int(cnt) if cnt else 5
        try:
            entity = await client.get_entity(entity_like)
        except ValueError as _:
            await client.send_message('me', 'User not found.')
        else:
            msgs = await client.get_messages(entity, limit=cnt)
            msgs.reverse()
            await client.forward_messages('me', msgs)

    elif command == 'flip_stickers':
        flip_stickers = not flip_stickers
        await msg.delete()
        await client.send_message(
            'me',
            'Now I{} flip stickers!'.format(
                '' if flip_stickers else ' don\'t'
            )
        )

    elif command == 'toggle_frame':
        frame_type = 'double' if frame_type == 'single' else 'single'
        await msg.delete()
        await client.send_message(
            'me',
            'Now using {} message frame'.format(frame_type)
        )

    elif command == 'toggle_dot':
        append_dot = not append_dot
        await client.send_message(
            'me',
            'Now I{} append dot to the end!'.format(
                '' if append_dot else ' don\'t'
            )
        )

    elif not msg.entities and command == 'fr':
        framed = utils.bordered(text, fr_type=frame_type)
        await msg.delete()
        await client.send_message(
            msg.chat_id,
            framed,
            parse_mode='HTML',
            link_preview='false',
            reply_to=msg.reply_to_msg_id
        )

    elif command in ('st', 'ст'):
        await msg.delete()
        _text = utils.to_staro_slav(text) if utils.is_cyrrillic(text) else text
        await msg.respond(_text, reply_to=msg.reply_to_msg_id)

    elif command == 'status':
        text = '\n'.join([
            f'Flipping stickers: {flip_stickers}',
            f'Frame type: {frame_type}',
            f'Appending dot: {append_dot}',
            f'Allow tag all: {allow_tag_all}'
        ])
        await client.send_message(
            'me',
            f'<code>{text}</code>',
            reply_to=msg.id,
            parse_mode='HTML'
        )

    elif command == 'help':
        await client.send_message('me', HELP_TEXT, reply_to=msg.id)

    elif command == 'flip':
        target: tl.custom.Message = await msg.get_reply_message()
        if (target and target.sticker):
            target.sticker
            await msg.delete()
            await flip_sticker(target)

    elif command == 'toggle_tagall':
        await msg.delete()
        allow_tag_all = not allow_tag_all
        await client.send_message(
            'me',
            'Now I{} allow tagging all participants'.format(
                '' if allow_tag_all else ' don\'t'
            )
        )

    if command == 'typing':
        try:
            await client.action(
                msg.chat.id,
                'typing',
            )
        except Exception as e:
            print(e)

    elif command == 'id':
        await msg.delete()
        reply = await msg.get_reply_message()
        text = ''
        if msg.is_group:
            chat = msg.chat
            text = f'<b>Chat</b>: {chat.title} [<code>{chat.id}</code>]\n'

        if reply is not None:
            sender: tl.types.User = reply.sender
            text += (
                f'<b>User</b>: {utils.mention(sender)} ' +
                f'[<code>{sender.id}</code>]\n'
            )
            text += f'<b>Message</b>: [<code>{reply.id}</code>]\n'
            # If message has any resource:
            if reply.sticker is not None:
                text += utils.repr_document('Sticker', reply.sticker)
            if reply.gif is not None:
                text += utils.repr_document('GIF', reply.gif)
            if reply.photo is not None:
                text += utils.repr_photo('Photo', reply.photo)

        await client.send_message('me', text, parse_mode='html')

    elif command == 'replace_unames':
        try:
            res = text
            for m in re.finditer(r'(@\S+)\s+(\S+)', text):
                username, replacement = m.groups()
                whole = m.group()
                users = [
                    u for u in
                    await client.get_participants(msg.chat.id, search=username)
                    if u.username == username[1:]
                ]
                res = res.replace(
                    whole,
                    f'<a href="tg://user?id={users[0].id}">{replacement}</a>'
                    if users
                    else username
                )

            await msg.delete()
            await client.send_message(
                msg.chat.id,
                res,
                parse_mode='HTML'
            )
        except Exception as e:
            print(e)

    elif not command and append_dot and text[-1].isalpha():
        await msg.delete()
        await msg.respond(
            text[0].upper() + text[1:] + '.',
            reply_to=msg.reply_to_msg_id
        )


async def on_new_message_other(event: events.NewMessage):
    msg: tl.custom.message.Message = event.message
    if (
        not msg.is_private and
        msg.sticker and
        msg.sticker.mime_type.endswith('webp') and
        flip_stickers
    ):
        await flip_sticker(msg)


async def on_new_message_all(event: events.NewMessage):
    msg: tl.custom.message.Message = event.message
    command, text = event.pattern_match.groups()
    voices = ['nicolai', 'maxim']

    if command in ('say', 'сей', 'гл'):
        if msg.out:
            await msg.delete()

        voicestr = '|'.join(voices)
        voice, phrase = re.search(
            fr'({voicestr})?\s*(.+)',
            text,
            re.DOTALL
        ).groups()

        input_name, temp_name = 'temp__.wav', 'temp__.ogg'

        data = {'phrase': phrase, 'voice': voice or 'nicolai'}
        try:
            resp = await http_client.post(
                f'{VOICE_API_URL}/say',
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
            stickers_map[msg.id] = (sent.chat_id, sent.id)

        os.unlink(temp_name)
        os.unlink(input_name)

    elif command == 'tagall' and allow_tag_all:
        users = await client.get_participants(msg.chat_id)
        if len(users) > TAG_ALL_LIMIT:
            return
        u: tl.types.User = {}
        msg_str = ' '.join(
            utils.mention(u)
            for u in users
            if not u.bot and not u.is_self
        )
        sent = await msg.respond(msg_str, parse_mode='HTML')
        stickers_map[msg.id] = (sent.chat_id, sent.id)

    match = re.search(
        r'^с такими приколами тебе сюда\s*:\s*(.+)',
        text,
        flags=re.IGNORECASE | re.DOTALL
    )
    if match:
        tuda = match[1]
        TEMP_FILE = 'wsj.jpg'
        pic = utils.with_such_jokes(tuda)
        pic.save(TEMP_FILE)
        sent = await msg.reply(file=TEMP_FILE)
        os.unlink(TEMP_FILE)
        stickers_map[msg.id] = (sent.chat_id, sent.id)


async def on_message_delete(event: events.MessageDeleted):
    global stickers_map
    stickerids = [i for i in event.deleted_ids if i in stickers_map]
    for _id in stickerids:
        chat_id, msg_id = stickers_map[_id]
        await client.delete_messages(chat_id, msg_id)
        del stickers_map[_id]


async def main():
    command_re = re.compile(r'\s*(?:\.(\w+))?\s*(.+)?', re.DOTALL)
    client.add_event_handler(
        on_new_message_me,
        event=events.NewMessage(pattern=command_re, outgoing=True)
    )
    client.add_event_handler(
        on_new_message_all,
        event=events.NewMessage(pattern=command_re)
    )
    client.add_event_handler(
        on_new_message_other,
        event=events.NewMessage(pattern=command_re, incoming=True)
    )
    client.add_event_handler(
        on_message_delete,
        event=events.MessageDeleted()
    )

    global http_client
    http_client = ClientSession(loop=client.loop)

    await client.start()
    print('Client started.')
    await client.run_until_disconnected()


async def shutdown():
    print('\nDisconnecting client.')
    await http_client.close()
    await client.disconnect()


if __name__ == '__main__':
    load_dotenv()

    VOICE_API_URL = os.getenv('VOICE_API_URL')
    JOKE_API_URL = os.getenv('JOKE_API_URL')
    client = make_client()
    loop = client.loop
    main_coro = main()
    exit_coro = shutdown()

    try:
        loop.run_until_complete(main_coro)
    except KeyboardInterrupt:
        loop.run_until_complete(exit_coro)
    finally:
        loop.close()
