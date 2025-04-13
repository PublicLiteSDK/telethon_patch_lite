import os
from typing import Optional, Union

from pydantic import BaseModel
from telethon.sessions import StringSession, SQLiteSession, MemorySession

from telethon_patch import helpers


class SessionContext:
    session: StringSession
    filename: Optional[str] = None

    @staticmethod
    def init(session: Union[SQLiteSession, StringSession]) -> "SessionContext":
        context = SessionContext()

        if isinstance(session, StringSession):
            context.session = session

        if isinstance(session, SQLiteSession):
            context.session = StringSession(helpers.build_session(
                dc=session.dc_id,
                ip=session.server_address,
                port=session.port,
                key=session.auth_key.key
            ))
            context.filename = session.filename

        if session is None:
            context.session = StringSession()

        return context
