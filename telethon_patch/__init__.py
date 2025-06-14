from telethon_patch.internal.lib.logging import logger, init_logging_config

init_logging_config()

###################
###################

from telethon_patch.internal.patches.patch import patch_telethon

patch_telethon()

###################
###################

from telethon_patch.models import InitContext, JsonContext

from telethon_patch.internal.storages import proxy_storage
from telethon_patch.internal.telegram_client.telegramclient import TelegramClient

__ALL__ = [
    TelegramClient,
    InitContext,
    JsonContext,
]
