import datetime
import ipaddress
import os
import re
import struct
import asyncio
import functools
import importlib.resources

from base64 import urlsafe_b64encode
from typing import Awaitable, Optional
from glob import glob

import dateutil.parser


def find_session_files(path: str, exclude_without_json: bool = True) -> dict[str, dict[str, str]]:
    session_files = glob(f"{path}/*.session") + glob(f"{path}/**/*.session", recursive=True)
    sessions = {os.path.basename(path).split(".")[0].lower(): path for path in session_files}

    json_files = glob(f"{path}/*.json") + glob(f"{path}/**/*.json", recursive=True)
    jsons = {os.path.basename(path).split(".")[0].lower(): path for path in json_files}

    return {
        file_name: dict(
            session_file=sessions[file_name],
            json_file=jsons.get(file_name)
        )
        for file_name in sessions
        if not exclude_without_json or file_name in jsons
    }


def open_text(path: str) -> str:
    with importlib.resources.open_text("telethon_patch.data", path) as file:
        return file.read()


def run_sync(func, *args, **kwargs) -> Awaitable:
    return asyncio.get_event_loop().run_in_executor(
        None, functools.partial(func, *args, **kwargs),
    )


def build_session(dc, ip, port, key) -> str:
    ip_bytes = ipaddress.ip_address(ip).packed
    data = struct.pack(">B4sH256s", dc, ip_bytes, port, key)
    encoded_data = urlsafe_b64encode(data).decode("ascii")
    return f"1{encoded_data}"


def extract_date_from_text_by_re(
        text,
        date_pattern: str = r"\b(\d{2})\.(\d{2})\.(\d{4})\b"
) -> Optional[datetime.datetime]:
    match = re.search(date_pattern, text)
    if match:
        day, month, year = map(int, match.groups())
        return datetime.datetime(year, month, day, tzinfo=datetime.UTC)


def extract_date_from_text(text) -> Optional[datetime.datetime]:
    try:
        date = dateutil.parser.parse(text, fuzzy=True)
        return datetime.datetime(
            date.year, date.month, date.day,
            date.hour, date.minute, date.second, tzinfo=datetime.UTC
        )
    except ValueError:
        return None
