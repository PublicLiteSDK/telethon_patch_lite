import struct
import asyncio

from telethon.errors import InvalidChecksumError, InvalidBufferError
from zlib import crc32

from telethon.network.connection.tcpfull import FullPacketCodec as FullPacketCodecOriginal


class FullPacketCodec(FullPacketCodecOriginal):
    async def read_packet(self, reader):
        try:
            packet_len_seq = await reader.readexactly(4)  # 4 and 4

        except asyncio.exceptions.IncompleteReadError:
            raise asyncio.CancelledError()

        if packet_len_seq == b'l\xfe\xff\xff':
            return packet_len_seq

        packet_len_seq += await reader.readexactly(4)

        packet_len, seq = struct.unpack('<ii', packet_len_seq)

        if packet_len < 0 and seq < 0:
            # It has been observed that the length and seq can be -429,
            # followed by the body of 4 bytes also being -429.
            # See https://github.com/LonamiWebs/Telethon/issues/4042.
            body = await reader.readexactly(4)
            raise InvalidBufferError(body)
        elif packet_len < 8:
            # Currently unknown why packet_len may be less than 8 but not negative.
            # Attempting to `readexactly` with less than 0 fails without saying what
            # the number was which is less helpful.
            raise InvalidBufferError(packet_len_seq)

        try:
            body = await reader.readexactly(packet_len - 8)

        except asyncio.exceptions.IncompleteReadError:
            raise asyncio.CancelledError()

        checksum = struct.unpack('<I', body[-4:])[0]
        body = body[:-4]

        valid_checksum = crc32(packet_len_seq + body)
        if checksum != valid_checksum:
            raise InvalidChecksumError(checksum, valid_checksum)

        return body
