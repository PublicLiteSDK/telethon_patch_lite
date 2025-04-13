import struct

from telethon.errors import UnauthorizedError, UserDeactivatedBanError, SessionRevokedError, AuthKeyNotFound, \
    AuthKeyDuplicatedError, ConnectionLayerInvalidError, BotMethodInvalidError

dead_errors = (
    UnauthorizedError,
    UserDeactivatedBanError,
    SessionRevokedError,
    AuthKeyNotFound,
    AuthKeyDuplicatedError,
    ConnectionLayerInvalidError,
    BotMethodInvalidError,
    struct.error
)
