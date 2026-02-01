#!/usr/bin/env python3
"""Compatibility wrapper for the Spotify DJ monitor.

The monitor implementation lives in the installable package at
`spotify_dj.monitor`. Keeping this tiny script at the repo root preserves the
historical `python monitor.py --latest` usage.
"""


def main() -> None:
    from spotify_dj.monitor import main as monitor_main

    monitor_main()


if __name__ == "__main__":
    main()
