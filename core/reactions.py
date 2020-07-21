from typing import Optional


class Base:
    def __init__(
        self,
        text: Optional[str] = None,
        clean_command=False
    ):
        pass

    def __call__(self):
        '''Executing reaction'''
        pass


class Message(Base):
    pass


class Media(Base):
    pass


class PlainText(Base):
    pass
