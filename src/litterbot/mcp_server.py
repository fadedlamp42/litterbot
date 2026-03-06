"""MCP server exposing Litter Robot control as tools.

provides tools for reading robot status/metrics and sending commands
via the Whisker cloud API. designed for stdio transport.
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from litterbot.account import connect_account, find_robot
from litterbot.robot import (
    extract_litter_robot_status,
    extract_robot_summary,
)

mcp = FastMCP(
    name="litterbot",
    instructions=(
        "controls Whisker Litter Robot devices via cloud API. "
        "use 'list_robots' first to discover available devices, "
        "then target specific robots by name or serial."
    ),
)


# -- helper to run operations against account --


async def _with_account(operation):
    """connect to account, run an async operation, disconnect, and return result."""
    account = await connect_account()
    try:
        return await operation(account)
    finally:
        await account.disconnect()


# -- read tools --


@mcp.tool(
    name="list_robots",
    description="list all Litter Robot devices on the account with basic info",
)
async def list_robots() -> str:
    """discover all robots linked to the Whisker account."""

    async def _list(account):
        results = []
        for robot in account.robots:
            results.append(extract_robot_summary(robot))
        return json.dumps(results, indent=2)

    return await _with_account(_list)


@mcp.tool(
    name="get_robot_status",
    description=(
        "get detailed status and metrics for a specific robot or all robots. "
        "includes cycle counts, drawer level, sleep mode, power status, etc."
    ),
)
async def get_robot_status(target: str | None = None) -> str:
    """get status for targeted robot(s). pass name or serial, or None for all."""
    from pylitterbot import LitterRobot

    async def _status(account):
        robots = find_robot(account, target)
        results = []
        for robot in robots:
            await robot.refresh()
            if isinstance(robot, LitterRobot):
                results.append(extract_litter_robot_status(robot))
            else:
                results.append(extract_robot_summary(robot))
        return json.dumps(results, indent=2)

    return await _with_account(_status)


@mcp.tool(
    name="get_activity_history",
    description="get recent activity history for a robot (clean cycles, drawer alerts, etc)",
)
async def get_activity_history(target: str | None = None, limit: int = 100) -> str:
    """return activity log. target by name/serial, or None for all."""
    from pylitterbot import LitterRobot

    async def _activity(account):
        robots = find_robot(account, target)
        all_results: dict[str, Any] = {}
        for robot in robots:
            if not isinstance(robot, LitterRobot):
                all_results[robot.name] = "activity history not supported for this robot type"
                continue
            activities = await robot.get_activity_history(limit=limit)
            all_results[robot.name] = [str(a) for a in activities]
        return json.dumps(all_results, indent=2)

    return await _with_account(_activity)


@mcp.tool(
    name="get_insight",
    description="get usage insight data (cycle counts per day, averages) for a robot",
)
async def get_insight(target: str | None = None, days: int = 30) -> str:
    """return insight summary. target by name/serial, or None for all."""
    from pylitterbot import LitterRobot

    async def _insight(account):
        robots = find_robot(account, target)
        all_results: dict[str, Any] = {}
        for robot in robots:
            if not isinstance(robot, LitterRobot):
                all_results[robot.name] = "insights not supported for this robot type"
                continue
            insight = await robot.get_insight(days=days)
            all_results[robot.name] = {
                "total_cycles": insight.total_cycles,
                "average_cycles": insight.average_cycles,
                "total_days": insight.total_days,
                "cycle_history": [{"date": str(d), "cycles": c} for d, c in insight.cycle_history],
            }
        return json.dumps(all_results, indent=2)

    return await _with_account(_insight)


@mcp.tool(
    name="get_raw_robot_data",
    description="dump raw robot data dict as JSON for debugging or deep inspection",
)
async def get_raw_robot_data(target: str | None = None) -> str:
    """return raw data dict. target by name/serial, or None for all."""

    async def _raw(account):
        robots = find_robot(account, target)
        results = {}
        for robot in robots:
            await robot.refresh()
            results[robot.name] = robot.to_dict()
        return json.dumps(results, indent=2, default=str)

    return await _with_account(_raw)


# -- write tools --


@mcp.tool(
    name="start_clean_cycle",
    description="start a clean cycle on a robot. target by name or serial, or None for all.",
)
async def start_clean_cycle(target: str | None = None) -> str:
    """trigger a clean cycle."""
    from pylitterbot import LitterRobot

    async def _clean(account):
        robots = find_robot(account, target)
        results = {}
        for robot in robots:
            if not isinstance(robot, LitterRobot):
                results[robot.name] = "not supported"
                continue
            ok = await robot.start_cleaning()
            results[robot.name] = "started" if ok else "failed"
        return json.dumps(results, indent=2)

    return await _with_account(_clean)


@mcp.tool(
    name="set_power",
    description="turn a robot on or off. state must be true (on) or false (off).",
)
async def set_power(state: bool, target: str | None = None) -> str:
    """set power state."""
    from pylitterbot import LitterRobot

    async def _power(account):
        robots = find_robot(account, target)
        results = {}
        for robot in robots:
            if not isinstance(robot, LitterRobot):
                results[robot.name] = "not supported"
                continue
            ok = await robot.set_power_status(state)
            results[robot.name] = "ok" if ok else "failed"
        return json.dumps(results, indent=2)

    return await _with_account(_power)


@mcp.tool(
    name="set_night_light",
    description="turn the night light on or off. state must be true (on) or false (off).",
)
async def set_night_light(state: bool, target: str | None = None) -> str:
    """set night light state."""

    async def _nightlight(account):
        robots = find_robot(account, target)
        results = {}
        for robot in robots:
            ok = await robot.set_night_light(state)
            results[robot.name] = "ok" if ok else "failed"
        return json.dumps(results, indent=2)

    return await _with_account(_nightlight)


@mcp.tool(
    name="set_panel_lock",
    description="enable or disable the panel lock. state must be true (locked) or false (unlocked).",
)
async def set_panel_lock(state: bool, target: str | None = None) -> str:
    """set panel lock state."""

    async def _lock(account):
        robots = find_robot(account, target)
        results = {}
        for robot in robots:
            ok = await robot.set_panel_lockout(state)
            results[robot.name] = "ok" if ok else "failed"
        return json.dumps(results, indent=2)

    return await _with_account(_lock)


@mcp.tool(
    name="set_wait_time",
    description="set the clean cycle wait time in minutes. valid values: 3, 7, or 15.",
)
async def set_wait_time(minutes: int, target: str | None = None) -> str:
    """set wait time before auto-clean after cat usage."""
    from pylitterbot import LitterRobot

    if minutes not in (3, 7, 15):
        return json.dumps({"error": "wait time must be 3, 7, or 15 minutes"})

    async def _wait(account):
        robots = find_robot(account, target)
        results = {}
        for robot in robots:
            if not isinstance(robot, LitterRobot):
                results[robot.name] = "not supported"
                continue
            ok = await robot.set_wait_time(minutes)
            results[robot.name] = "ok" if ok else "failed"
        return json.dumps(results, indent=2)

    return await _with_account(_wait)


@mcp.tool(
    name="set_sleep_mode",
    description="enable or disable sleep mode. state must be true (on) or false (off).",
)
async def set_sleep_mode(state: bool, target: str | None = None) -> str:
    """toggle sleep mode."""
    from pylitterbot import LitterRobot

    async def _sleep(account):
        robots = find_robot(account, target)
        results = {}
        for robot in robots:
            if not isinstance(robot, LitterRobot):
                results[robot.name] = "not supported"
                continue
            ok = await robot.set_sleep_mode(state)
            results[robot.name] = "ok" if ok else "failed"
        return json.dumps(results, indent=2)

    return await _with_account(_sleep)


@mcp.tool(
    name="rename_robot",
    description="rename a specific robot. requires target (name or serial) to identify which robot.",
)
async def rename_robot(new_name: str, target: str) -> str:
    """rename a robot. target is required."""

    async def _rename(account):
        robots = find_robot(account, target)
        results = {}
        for robot in robots:
            ok = await robot.set_name(new_name)
            results[robot.serial] = "ok" if ok else "failed"
        return json.dumps(results, indent=2)

    return await _with_account(_rename)


if __name__ == "__main__":
    mcp.run(transport="stdio")
