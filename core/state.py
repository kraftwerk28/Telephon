from typing import Tuple, Dict


class State:
    '''Tgai serializable state'''

    def __init__(self):
        self.autorm: Dict[int, Tuple[int, int]] = {}

    def __repr__(self):
        return 'State: ' + repr(vars(self))

    def save(self):
        pass

    def restore():
        return State()
