"""Command registry and command ID definitions."""

from enum import IntEnum
from typing import Dict
from .base import CommandSpec


class CommandId(IntEnum):
    """BMS command identifiers combining hi/lo bytes."""
    READ_TOTAL_VOLTAGE = 0x0300
    READ_CELL_VOLTAGE = 0x0301
    READ_CURRENT = 0x0302


COMMANDS: Dict[CommandId, CommandSpec] = {}