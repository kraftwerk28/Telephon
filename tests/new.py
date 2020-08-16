import os
import sys
import logging as log
from dotenv import load_dotenv

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
config = InitConfig(SESSION_PATH, API_ID, API_HASH)
app = Telephon(config)


@app.on_command('help', named_args=['object', 'sample'])
async def help(ctx: Context):
    await ctx.reply(f'Named args: {str(ctx.named_args)}',
                    reply=True,
                    delete_command_message=True)
    # print(ctx.state)
    # await ctx.msg.reply(
    #     'Help: {}, {}'.format(
    #         ctx.named_args['object'],
    #         ctx.named_args['sample'],
    #     )
    # )


# @app.on_command('tagall')
# async def tagall(ctx: Context):
#     users = await ctx.client.get_participants(ctx.msg.chat_id)
#     if len(users) > 50:
#         return
#     mentions = [utils.mention(u) for u in users if not u.bot and not u.is_self]
#     if mentions:
#         sent = await ctx.msg.respond(' '.join(mentions))
#         ctx.state.autorm[ctx.msg.id] = (sent.chat_id, sent.id)


# @app.on_command(['say', 'гл'])
# async def voice_engine(ctx: Context):
#     if ctx.msg.out:
#         await ctx.msg.delete()
#     voice, *rest = ctx.args
#     phrase = ' '.join(rest)
#     await ctx.msg.respond(f'{voice}: {phrase}')


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

def mention(user: tl.types.User, with_link=False):
    if user.username:
        return f'@{user.username}'
    name = user.first_name
    if user.last_name:
        name += ' ' + user.last_name
    if with_link:
        return f'<a href="tg://user?id={user.id}">{name}</a>'
    return name


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
