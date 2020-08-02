import re

COMMAND_PREFIX = r'\.'
SUBCMD_LEFT_BRACKET = r'\['
SUBCMD_RIGHT_BRACKET = r'\]'
CMD_SPLIT_REGEX = re.compile(
    '|'.join([r'\s+',
              fr'({SUBCMD_LEFT_BRACKET})',
              fr'({SUBCMD_RIGHT_BRACKET})']))
