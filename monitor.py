#!/usr/bin/env python3
"""
Spotify DJ Monitor Dashboard.
Tails the latest debug log session and displays real-time status using Rich.
"""

import argparse
import glob
import json
import os
import sys
import time
from collections import deque
from datetime import datetime

from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.console import Console


class DashboardState:
    def __init__(self):
        self.track_title = "Unknown Title"
        self.track_artist = "Unknown Artist"
        self.progress_ms = 0
        self.duration_ms = 1
        self.time_until_injection = 0

        self.queue_remaining = 0
        self.next_songs = []

        self.last_injection_time = None
        self.should_inject = False
        self.already_injected = False

        self.events = deque(maxlen=10)
        self.errors = deque(maxlen=5)

        self.last_update_ts = time.time()
        self.connected_file = ""


def make_layout():
    layout = Layout(name="root")

    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=10),
    )

    layout["main"].split_row(
        Layout(name="left", ratio=1), Layout(name="right", ratio=1)
    )

    layout["left"].split_column(
        Layout(name="now_playing", size=7),
        Layout(name="shadow_queue", ratio=1),
        Layout(name="injection_status", size=6),
    )

    layout["right"].split_column(
        Layout(name="events_log", ratio=2), Layout(name="errors_log", ratio=1)
    )

    return layout


def format_time(seconds):
    if seconds is None:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def generate_now_playing_panel(state):
    progress_percent = (
        min(100, max(0, (state.progress_ms / state.duration_ms) * 100))
        if state.duration_ms > 0
        else 0
    )

    width = 30
    filled = int(width * (progress_percent / 100))
    bar = "━" * filled + "─" * (width - filled)

    content = Text()
    content.append("Title: ", style="bold cyan")
    content.append(f"{state.track_title}\n")
    content.append("Artist: ", style="bold cyan")
    content.append(f"{state.track_artist}\n")
    content.append(f"{bar} {int(progress_percent)}%\n", style="green")
    content.append("Time until injection: ", style="bold yellow")
    content.append(f"{state.time_until_injection}s", style="yellow")

    return Panel(content, title="NOW PLAYING", border_style="blue")


def generate_shadow_queue_panel(state):
    content = Text()
    content.append("Remaining: ", style="bold")
    content.append(f"{state.queue_remaining} songs\n\n", style="white")

    content.append("Next Up:\n", style="bold underline")
    if not state.next_songs:
        content.append(" (Empty)", style="dim")
    else:
        for i, song in enumerate(state.next_songs[:3]):
            if isinstance(song, dict):
                title = song.get("title", "Unknown")
                artist = song.get("artist", "Unknown")
                display = f"{title} - {artist}"
            else:
                display = str(song)
            content.append(f" {i + 1}. {display}\n")

    return Panel(content, title="SHADOW QUEUE", border_style="magenta")


def generate_injection_status_panel(state):
    content = Text()

    content.append("Last injection: ", style="bold")
    if state.last_injection_time:
        ago = int(time.time() - state.last_injection_time)
        content.append(f"{ago}s ago\n")
    else:
        content.append("Never\n")

    content.append("State: ", style="bold")
    if state.should_inject:
        content.append("READY TO INJECT", style="bold green")
    else:
        content.append("Waiting", style="dim")
    content.append("\n")

    content.append("Already injected: ", style="bold")
    content.append(
        "Yes" if state.already_injected else "No",
        style="yellow" if state.already_injected else "green",
    )

    return Panel(content, title="INJECTION STATUS", border_style="yellow")


def generate_events_panel(state):
    content = Text()
    for ts, event_type, details in state.events:
        time_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
        content.append(f"[{time_str}] ", style="dim")
        content.append(f"{event_type}: ", style="bold blue")
        content.append(f"{str(details)}\n")

    return Panel(
        content, title=f"EVENTS LOG (Last {len(state.events)})", border_style="white"
    )


def generate_errors_panel(state):
    content = Text()
    if not state.errors:
        content.append("No errors", style="green")
    else:
        for ts, error_msg in state.errors:
            time_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
            content.append(f"[{time_str}] {error_msg}\n", style="bold red")

    return Panel(content, title="ERRORS", border_style="red")


def generate_header(state, filename):
    table = Text()
    table.append("SPOTIFY DJ MONITOR", style="bold green reverse")
    table.append(f"  Watching: {filename}", style="italic")

    time_since_update = time.time() - state.last_update_ts
    if time_since_update > 30:
        table.append(
            f"  ⚠️  No updates in {int(time_since_update)}s", style="bold red blink"
        )

    return Panel(table, box=None)


def get_log_file(args):
    """Resolve the log file path based on arguments."""
    if args.file:
        return args.file

    if args.latest:
        files = glob.glob("logs/session_*.jsonl")
        if not files:
            return None
        return max(files, key=os.path.getmtime)

    return None


def parse_line(line, state):
    """Parse a single JSONL line and update state."""
    try:
        data = json.loads(line.strip())
        state.last_update_ts = time.time()

        if "cycle_num" in data:
            playing = data.get("playing", {})
            state.track_title = playing.get("title", "Unknown")
            state.track_artist = playing.get("artist", "Unknown")
            state.progress_ms = playing.get("progress_ms", 0) or 0
            state.duration_ms = playing.get("duration_ms", 1) or 1

            shadow = data.get("shadow_queue", {})
            state.queue_remaining = shadow.get("remaining", 0)
            next_s = shadow.get("next_song")
            if next_s:
                state.next_songs = [next_s]
            else:
                state.next_songs = []

            injection = data.get("injection_state", {})
            state.time_until_injection = injection.get("time_until_end", 0)
            state.should_inject = injection.get("should_inject", False)
            state.already_injected = injection.get("already_injected", False)

            if state.should_inject and not state.already_injected:
                pass

        elif data.get("type") == "error":
            state.errors.append(
                (data.get("timestamp", time.time()), data.get("error", "Unknown error"))
            )

        else:
            evt_type = data.get("type", "unknown")
            details = data.get("data", {})
            ts = time.time()
            if isinstance(details, dict):
                ts = details.get("timestamp", ts)

            state.events.append((ts, evt_type, details))

            if evt_type == "injection":
                state.last_injection_time = ts

    except json.JSONDecodeError:
        print("Warning: Malformed line, skipping...", file=sys.stderr)
    except Exception as e:
        state.errors.append((time.time(), f"Monitor Parse Error: {str(e)}"))


def main():
    parser = argparse.ArgumentParser(description="Spotify DJ Monitor")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Specific log file path")
    group.add_argument(
        "--latest", action="store_true", help="Watch most recent log file"
    )

    args = parser.parse_args()

    console = Console()
    state = DashboardState()

    log_path = None
    while log_path is None:
        log_path = get_log_file(args)
        if log_path is None or not os.path.exists(log_path):
            console.print("[yellow]Waiting for log file to appear...[/yellow]")
            time.sleep(1)
            if args.file and not os.path.exists(args.file):
                log_path = None
            elif args.latest:
                log_path = get_log_file(args)

    state.connected_file = log_path

    try:
        f = open(log_path, "r")
        for line in f:
            parse_line(line, state)

    except Exception as e:
        console.print(f"[bold red]Error opening file: {e}[/bold red]")
        sys.exit(1)

    layout = make_layout()

    try:
        with Live(layout, refresh_per_second=10, screen=True) as live:
            while True:
                while True:
                    line = f.readline()
                    if not line:
                        break
                    parse_line(line, state)

                layout["header"].update(generate_header(state, log_path))
                layout["now_playing"].update(generate_now_playing_panel(state))
                layout["shadow_queue"].update(generate_shadow_queue_panel(state))
                layout["injection_status"].update(
                    generate_injection_status_panel(state)
                )
                layout["events_log"].update(generate_events_panel(state))
                layout["errors_log"].update(generate_errors_panel(state))

                time.sleep(0.1)

    except KeyboardInterrupt:
        console.print("\n[bold green]Exiting monitor...[/bold green]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Fatal error: {e}[/bold red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
