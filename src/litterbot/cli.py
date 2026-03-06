"""argparse CLI for controlling Litter Robot devices.

supports both single-device targeting (--target) and broadcast to all devices (default).
all subcommands run against the Whisker cloud API via pylitterbot.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from prism.logging import configure_logging, get_logger

from litterbot.account import CredentialError, connect_account, find_robot
from litterbot.robot import (
    extract_litter_robot_status,
    extract_robot_summary,
    format_activity_history,
    format_insight,
    format_robot_status,
)

logger = get_logger()


# -- read commands --


async def command_status(args: argparse.Namespace) -> None:
    """print status of all targeted robots."""
    account = await connect_account()
    try:
        robots = find_robot(account, args.target)
        for robot in robots:
            await robot.refresh()
            if args.json:
                from pylitterbot import LitterRobot

                if isinstance(robot, LitterRobot):
                    print(json.dumps(extract_litter_robot_status(robot), indent=2))
                else:
                    print(json.dumps(extract_robot_summary(robot), indent=2))
            else:
                print(format_robot_status(robot))
            if robot != robots[-1]:
                print()
    finally:
        await account.disconnect()


async def command_list(args: argparse.Namespace) -> None:
    """list all robots on the account."""
    account = await connect_account()
    try:
        for robot in account.robots:
            if args.json:
                print(json.dumps(extract_robot_summary(robot), indent=2))
            else:
                print(
                    "%(name)s | %(model)s | %(serial)s | %(online)s"
                    % {
                        "name": robot.name,
                        "model": robot.model,
                        "serial": robot.serial,
                        "online": "online" if robot.is_online else "offline",
                    }
                )
    finally:
        await account.disconnect()


async def command_activity(args: argparse.Namespace) -> None:
    """print activity history for targeted robots."""
    from pylitterbot import LitterRobot

    account = await connect_account()
    try:
        robots = find_robot(account, args.target)
        for robot in robots:
            if not isinstance(robot, LitterRobot):
                print("%(name)s: activity history not supported" % {"name": robot.name})
                continue
            activities = await robot.get_activity_history(limit=args.limit)
            print("%(name)s:" % {"name": robot.name})
            if args.json:
                print(json.dumps([str(a) for a in activities], indent=2))
            else:
                print(format_activity_history(activities))
            if robot != robots[-1]:
                print()
    finally:
        await account.disconnect()


async def command_insight(args: argparse.Namespace) -> None:
    """print insight data for targeted robots."""
    from pylitterbot import LitterRobot

    account = await connect_account()
    try:
        robots = find_robot(account, args.target)
        for robot in robots:
            if not isinstance(robot, LitterRobot):
                print("%(name)s: insights not supported" % {"name": robot.name})
                continue
            insight = await robot.get_insight(days=args.days)
            print("%(name)s:" % {"name": robot.name})
            if args.json:
                print(
                    json.dumps(
                        {
                            "total_cycles": insight.total_cycles,
                            "average_cycles": insight.average_cycles,
                            "total_days": insight.total_days,
                            "cycle_history": [
                                {"date": str(d), "cycles": c} for d, c in insight.cycle_history
                            ],
                        },
                        indent=2,
                    )
                )
            else:
                print(format_insight(insight))
            if robot != robots[-1]:
                print()
    finally:
        await account.disconnect()


async def command_raw(args: argparse.Namespace) -> None:
    """dump raw robot data as JSON for debugging."""
    account = await connect_account()
    try:
        robots = find_robot(account, args.target)
        for robot in robots:
            await robot.refresh()
            print(json.dumps(robot.to_dict(), indent=2, default=str))
            if robot != robots[-1]:
                print()
    finally:
        await account.disconnect()


# -- write commands --


async def command_clean(args: argparse.Namespace) -> None:
    """start a clean cycle on targeted robots."""
    from pylitterbot import LitterRobot

    account = await connect_account()
    try:
        robots = find_robot(account, args.target)
        for robot in robots:
            if not isinstance(robot, LitterRobot):
                print("%(name)s: clean not supported" % {"name": robot.name})
                continue
            result = await robot.start_cleaning()
            print(
                "%(name)s: clean cycle %(result)s"
                % {"name": robot.name, "result": "started" if result else "failed"}
            )
    finally:
        await account.disconnect()


async def command_power(args: argparse.Namespace) -> None:
    """set power state on targeted robots."""
    from pylitterbot import LitterRobot

    account = await connect_account()
    try:
        robots = find_robot(account, args.target)
        value = args.state == "on"
        for robot in robots:
            if not isinstance(robot, LitterRobot):
                print("%(name)s: power control not supported" % {"name": robot.name})
                continue
            result = await robot.set_power_status(value)
            print(
                "%(name)s: power %(state)s %(result)s"
                % {
                    "name": robot.name,
                    "state": args.state,
                    "result": "ok" if result else "failed",
                }
            )
    finally:
        await account.disconnect()


async def command_nightlight(args: argparse.Namespace) -> None:
    """set night light on targeted robots."""
    account = await connect_account()
    try:
        robots = find_robot(account, args.target)
        value = args.state == "on"
        for robot in robots:
            result = await robot.set_night_light(value)
            print(
                "%(name)s: night light %(state)s %(result)s"
                % {
                    "name": robot.name,
                    "state": args.state,
                    "result": "ok" if result else "failed",
                }
            )
    finally:
        await account.disconnect()


async def command_panel_lock(args: argparse.Namespace) -> None:
    """set panel lock on targeted robots."""
    account = await connect_account()
    try:
        robots = find_robot(account, args.target)
        value = args.state == "on"
        for robot in robots:
            result = await robot.set_panel_lockout(value)
            print(
                "%(name)s: panel lock %(state)s %(result)s"
                % {
                    "name": robot.name,
                    "state": args.state,
                    "result": "ok" if result else "failed",
                }
            )
    finally:
        await account.disconnect()


async def command_wait_time(args: argparse.Namespace) -> None:
    """set clean cycle wait time on targeted robots."""
    from pylitterbot import LitterRobot

    account = await connect_account()
    try:
        robots = find_robot(account, args.target)
        for robot in robots:
            if not isinstance(robot, LitterRobot):
                print("%(name)s: wait time not supported" % {"name": robot.name})
                continue
            result = await robot.set_wait_time(args.minutes)
            print(
                "%(name)s: wait time set to %(minutes)s min %(result)s"
                % {
                    "name": robot.name,
                    "minutes": args.minutes,
                    "result": "ok" if result else "failed",
                }
            )
    finally:
        await account.disconnect()


async def command_sleep_mode(args: argparse.Namespace) -> None:
    """set sleep mode on targeted robots."""
    from pylitterbot import LitterRobot

    account = await connect_account()
    try:
        robots = find_robot(account, args.target)
        value = args.state == "on"
        for robot in robots:
            if not isinstance(robot, LitterRobot):
                print("%(name)s: sleep mode not supported" % {"name": robot.name})
                continue
            result = await robot.set_sleep_mode(value)
            print(
                "%(name)s: sleep mode %(state)s %(result)s"
                % {
                    "name": robot.name,
                    "state": args.state,
                    "result": "ok" if result else "failed",
                }
            )
    finally:
        await account.disconnect()


async def command_rename(args: argparse.Namespace) -> None:
    """rename a targeted robot."""
    account = await connect_account()
    try:
        robots = find_robot(account, args.target)
        if len(robots) > 1 and args.target is None:
            print("error: --target is required for rename (can't rename all robots at once)")
            return
        for robot in robots:
            result = await robot.set_name(args.name)
            print(
                "%(serial)s: renamed to '%(name)s' %(result)s"
                % {
                    "serial": robot.serial,
                    "name": args.name,
                    "result": "ok" if result else "failed",
                }
            )
    finally:
        await account.disconnect()


# -- parser setup --


def build_parser() -> argparse.ArgumentParser:
    """build the argparse parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="litterbot",
        description="control Whisker Litter Robot devices via cloud API",
    )
    parser.add_argument(
        "--target",
        "-t",
        help="target a specific robot by name or serial (default: all robots)",
        default=None,
    )
    parser.add_argument(
        "--json",
        "-j",
        help="output in JSON format where supported",
        action="store_true",
        default=False,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # -- read subcommands --
    subparsers.add_parser("status", help="show robot status and metrics")
    subparsers.add_parser("list", help="list all robots on the account")

    activity_parser = subparsers.add_parser("activity", help="show activity history")
    activity_parser.add_argument(
        "--limit", "-l", type=int, default=100, help="max entries to return (default: 100)"
    )

    insight_parser = subparsers.add_parser("insight", help="show usage insights")
    insight_parser.add_argument(
        "--days", "-d", type=int, default=30, help="number of days to analyze (default: 30)"
    )

    subparsers.add_parser("raw", help="dump raw robot data as JSON")

    # -- write subcommands --
    subparsers.add_parser("clean", help="start a clean cycle")

    power_parser = subparsers.add_parser("power", help="set power state")
    power_parser.add_argument("state", choices=["on", "off"])

    nightlight_parser = subparsers.add_parser("nightlight", help="set night light")
    nightlight_parser.add_argument("state", choices=["on", "off"])

    lock_parser = subparsers.add_parser("lock", help="set panel lock")
    lock_parser.add_argument("state", choices=["on", "off"])

    wait_parser = subparsers.add_parser("wait-time", help="set clean cycle wait time")
    wait_parser.add_argument("minutes", type=int, choices=[3, 7, 15])

    sleep_parser = subparsers.add_parser("sleep", help="set sleep mode")
    sleep_parser.add_argument("state", choices=["on", "off"])

    rename_parser = subparsers.add_parser("rename", help="rename a robot")
    rename_parser.add_argument("name", help="new name for the robot")

    return parser


COMMAND_MAP = {
    "status": command_status,
    "list": command_list,
    "activity": command_activity,
    "insight": command_insight,
    "raw": command_raw,
    "clean": command_clean,
    "power": command_power,
    "nightlight": command_nightlight,
    "lock": command_panel_lock,
    "wait-time": command_wait_time,
    "sleep": command_sleep_mode,
    "rename": command_rename,
}


def main() -> None:
    """entry point for the litterbot CLI."""
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()

    handler = COMMAND_MAP.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    try:
        asyncio.run(handler(args))
    except CredentialError as err:
        print("error: %(msg)s" % {"msg": err}, file=sys.stderr)
        sys.exit(1)
    except ValueError as err:
        print("error: %(msg)s" % {"msg": err}, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
