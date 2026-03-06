"""account connection and robot discovery via Whisker cloud API.

wraps pylitterbot.Account with credential management and convenience helpers
for connecting, discovering robots, and targeting specific devices.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from prism.logging import get_logger
from pylitterbot import Account

if TYPE_CHECKING:
    from pylitterbot.robot import Robot

logger = get_logger()


class CredentialError(Exception):
    """raised when Whisker credentials are missing or invalid."""


def get_credentials() -> tuple[str, str]:
    """read Whisker credentials from environment variables.

    returns (username, password) tuple. raises CredentialError if not set.
    """
    username = os.environ.get("LITTERBOT_USERNAME", "")
    password = os.environ.get("LITTERBOT_PASSWORD", "")
    if not username or not password:
        raise CredentialError(
            "LITTERBOT_USERNAME and LITTERBOT_PASSWORD environment variables are required"
        )
    return username, password


async def connect_account() -> Account:
    """authenticate and load all robots for the configured account.

    reads credentials from LITTERBOT_USERNAME and LITTERBOT_PASSWORD env vars.
    returns a connected Account with robots loaded.
    """
    username, password = get_credentials()
    account = Account()
    await account.connect(
        username=username,
        password=password,
        load_robots=True,
    )
    logger.info(
        "connected to whisker account",
        robot_count=len(account.robots),
    )
    return account


def find_robot(account: Account, target: str | None) -> list[Robot]:
    """resolve a target string to a list of robots.

    if target is None, returns all robots (broadcast).
    if target matches a robot name (case-insensitive) or serial, returns that single robot.
    raises ValueError if target doesn't match any robot.
    """
    if target is None:
        return list(account.robots)

    target_lower = target.lower()
    for robot in account.robots:
        if robot.name.lower() == target_lower or robot.serial.lower() == target_lower:
            return [robot]

    available = ", ".join(
        "%(name)s (%(serial)s)" % {"name": r.name, "serial": r.serial} for r in account.robots
    )
    raise ValueError(
        "no robot matching '%(target)s'; available: %(available)s"
        % {"target": target, "available": available}
    )
