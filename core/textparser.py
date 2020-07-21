from telethon.events import NewMessage

class TextParse:
    def __init__(self, event: NewMessage):
        text = event.message.text
