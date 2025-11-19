from __future__ import annotations

import importlib
import importlib.util
import importlib.machinery
import pkgutil
import sys
import types
from pathlib import Path
from typing import List, Type

from .arbiter import BoardConfig


def load_package(path: str, name: str) -> types.ModuleType:
    p = Path(path).resolve()
    if not p.exists():
        raise ValueError(f"Missing directory: {p}")

    spec = importlib.machinery.ModuleSpec(name=name, loader=None, is_package=True)
    module = importlib.util.module_from_spec(spec)
    module.__path__ = [str(p)]
    sys.modules[name] = module
    return module


def discover_board_modules(pkg: types.ModuleType):
    result = []
    for info in pkgutil.iter_modules(pkg.__path__):
        mod = importlib.import_module(f"{pkg.__name__}.{info.name}")
        if hasattr(mod, "BOARD_NAME"):
            result.append(mod)
    return result


def board_module_to_config(mod) -> BoardConfig:
    return BoardConfig(
        name=mod.BOARD_NAME,
        width=mod.BOARD_WIDTH,
        height=mod.BOARD_HEIGHT,
        win_length=mod.WIN_LENGTH,
        num_players=mod.NUM_PLAYERS,
        obstacles=list(mod.OBSTACLES),
        time_ms=mod.GAME_TIME_MS,
    )


def discover_bot_classes(bots_pkg: types.ModuleType) -> List[Type]:
    base = importlib.import_module(f"{bots_pkg.__name__}.base_bot").BaseBot
    result: List[Type] = []

    for info in pkgutil.iter_modules(bots_pkg.__path__):
        if info.name == "base_bot":
            continue

        mod = importlib.import_module(f"{bots_pkg.__name__}.{info.name}")

        # Find all classes in this module that inherit from BaseBot
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if isinstance(attr, type) and issubclass(attr, base) and attr is not base:
                result.append(attr)

    return result
