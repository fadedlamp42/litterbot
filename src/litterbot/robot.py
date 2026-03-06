"""robot state extraction and formatting utilities.

provides pure functions for reading robot properties into structured dicts
and formatting them for human-readable output.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pylitterbot import LitterRobot

if TYPE_CHECKING:
    from pylitterbot.robot import Robot


def extract_robot_summary(robot: Robot) -> dict[str, Any]:
    """extract a summary dict of basic robot info.

    works for any robot type (LitterRobot, FeederRobot, etc).
    """
    summary: dict[str, Any] = {
        "name": robot.name,
        "model": robot.model,
        "serial": robot.serial,
        "id": robot.id,
        "is_online": robot.is_online,
        "night_light_mode_enabled": robot.night_light_mode_enabled,
        "panel_lock_enabled": robot.panel_lock_enabled,
        "power_status": robot.power_status,
    }

    setup_date = robot.setup_date
    if setup_date is not None:
        summary["setup_date"] = setup_date.isoformat()

    return summary


def extract_litter_robot_status(robot: LitterRobot) -> dict[str, Any]:
    """extract full status dict for a LitterRobot (LR3, LR4, LR5).

    includes all metrics: cycle counts, drawer level, sleep mode, etc.
    """
    status = extract_robot_summary(robot)

    status.update(
        {
            "status": robot.status.value,
            "status_text": robot.status_text,
            "clean_cycle_wait_time_minutes": robot.clean_cycle_wait_time_minutes,
            "cycle_capacity": robot.cycle_capacity,
            "cycle_count": robot.cycle_count,
            "cycles_after_drawer_full": robot.cycles_after_drawer_full,
            "waste_drawer_level": robot.waste_drawer_level,
            "is_drawer_full_indicator_triggered": robot.is_drawer_full_indicator_triggered,
            "is_waste_drawer_full": robot.is_waste_drawer_full,
            "is_sleeping": robot.is_sleeping,
            "sleep_mode_enabled": robot.sleep_mode_enabled,
        }
    )

    last_seen = robot.last_seen
    if last_seen is not None:
        status["last_seen"] = last_seen.isoformat()

    sleep_start = robot.sleep_mode_start_time
    sleep_end = robot.sleep_mode_end_time
    if sleep_start is not None:
        status["sleep_mode_start_time"] = sleep_start.isoformat()
    if sleep_end is not None:
        status["sleep_mode_end_time"] = sleep_end.isoformat()

    return status


def format_robot_status(robot: Robot) -> str:
    """format robot status as a human-readable multi-line string."""
    if isinstance(robot, LitterRobot):
        status = extract_litter_robot_status(robot)
    else:
        status = extract_robot_summary(robot)

    lines = ["%(name)s (%(serial)s)" % {"name": status["name"], "serial": status["serial"]}]
    lines.append("  model: %(model)s" % {"model": status["model"]})
    lines.append("  online: %(online)s" % {"online": status["is_online"]})
    lines.append("  power: %(power)s" % {"power": status["power_status"]})

    if isinstance(robot, LitterRobot):
        lines.append(
            "  status: %(text)s (%(code)s)"
            % {"text": status["status_text"], "code": status["status"]}
        )
        lines.append("  drawer: %(level).0f%% full" % {"level": status["waste_drawer_level"]})
        lines.append(
            "  cycles: %(count)s / %(capacity)s"
            % {"count": status["cycle_count"], "capacity": status["cycle_capacity"]}
        )
        lines.append(
            "  wait time: %(wait)s min" % {"wait": status["clean_cycle_wait_time_minutes"]}
        )
        lines.append("  night light: %(nl)s" % {"nl": status["night_light_mode_enabled"]})
        lines.append("  panel lock: %(lock)s" % {"lock": status["panel_lock_enabled"]})
        lines.append("  sleep mode: %(sleep)s" % {"sleep": status["sleep_mode_enabled"]})
        if "last_seen" in status:
            lines.append("  last seen: %(seen)s" % {"seen": status["last_seen"]})

    return "\n".join(lines)


def format_activity_history(activities: list) -> str:
    """format activity history entries as human-readable lines."""
    if not activities:
        return "no activity history"

    lines = []
    for activity in activities:
        lines.append(str(activity))
    return "\n".join(lines)


def format_insight(insight) -> str:
    """format insight data as a human-readable summary."""
    lines = [str(insight)]
    if insight.cycle_history:
        lines.append("daily breakdown:")
        for cycle_date, count in insight.cycle_history:
            date_string = (
                cycle_date.isoformat() if isinstance(cycle_date, datetime) else str(cycle_date)
            )
            lines.append("  %(date)s: %(count)s cycles" % {"date": date_string, "count": count})
    return "\n".join(lines)
