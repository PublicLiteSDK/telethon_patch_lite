from .tools import (
    FilesMethods, ClientMethods
)
from .telegrambaseclient import (
    TelegramBaseV2Client
)


class TelegramClient(
    FilesMethods, ClientMethods, TelegramBaseV2Client
):
    pass
