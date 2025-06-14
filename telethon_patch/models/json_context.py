import os
from typing import Optional, Union

from pydantic import BaseModel

from telethon_patch.lib import helpers


class JsonContent(BaseModel):
    app_id: Optional[int] = None
    app_hash: Optional[str] = None

    sdk: Optional[str] = None
    device: Optional[str] = None
    app_version: Optional[str] = None

    lang_pack: Optional[str] = None
    system_lang_pack: Optional[str] = None

    twoFA: Optional[str] = None
    role: Optional[str] = None

    id: Optional[int] = None
    phone: Optional[str] = None
    username: Optional[str] = None

    date_of_birth: Optional[int] = None
    date_of_birth_integrity: Optional[str] = None

    is_premium: Optional[bool] = None
    premium_expiry: Optional[int] = None

    first_name: Optional[str] = None
    last_name: Optional[str] = None

    has_profile_pic: Optional[bool] = None

    spamblock: Optional[str] = None
    spamblock_end_date: Optional[str] = None

    session_file: Optional[str] = None
    stats_spam_count: Optional[int] = None
    stats_invites_count: Optional[int] = None
    last_connect_date: Optional[str] = None
    session_created_date: Optional[str] = None

    user_id: Optional[int] = None
    device_token: Optional[str] = None
    device_token_secret: Optional[str] = None
    device_secret: Optional[str] = None
    signature: Optional[str] = None
    certificate: Optional[str] = None
    safetynet: Optional[str] = None
    perf_cat: Optional[int] = None
    tz_offset: Optional[int] = None

    register_time: Optional[float] = None
    last_check_time: Optional[float] = None

    avatar: Optional[str] = None
    sex: Optional[int] = None

    proxy: Optional[Union[str, list]] = None
    ipv6: Optional[bool] = None

    time: Optional[str] = None

    extra_params: Optional[str] = None
    freeze_integrity: Optional[str] = None
    freeze_appeal_url: Optional[str] = None
    freeze_until: Optional[str] = None
    freeze_since: Optional[str] = None


class JsonContext:
    content: JsonContent
    filename: str

    @staticmethod
    def _sync_load_json_file(filename: str) -> "JsonContext":
        with open(filename, mode='r', encoding='utf-8') as file:
            content = file.read()

        context = JsonContext()
        context.content = JsonContent.model_validate_json(content)
        context.filename = filename

        return context

    @staticmethod
    async def load_json_file(filename: str) -> "JsonContext":
        return await helpers.run_sync(JsonContext._sync_load_json_file, filename=filename)

    def _sync_dump_json_file(self, **kwargs) -> "JsonContext":
        if self.filename is None or os.path.isfile(self.filename) is False:
            return None

        for key, value in kwargs.items():
            setattr(self.content, key, value)

        content = self.content.model_dump_json(indent=4)
        with open(self.filename, mode='w', encoding='utf-8') as file:
            file.write(content)

        return self

    async def dump_json_file(self, **kwargs) -> "JsonContext":
        return await helpers.run_sync(self._sync_dump_json_file, **kwargs)
