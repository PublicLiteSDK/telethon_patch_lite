from . import code

from telethon.network.connection.tcpfull import FullPacketCodec
from telethon.network import MTProtoSender
from telethon.client.telegrambaseclient import TelegramBaseClient

injected = False


def patch_telethon():
    global injected

    if injected is False:
        FullPacketCodec.read_packet = code.tcpfull.FullPacketCodec.read_packet
        MTProtoSender._disconnect = code.mtprotosender.MTProtoSender._disconnect
        TelegramBaseClient.connect = code.telegrambaseclient.TelegramBaseClient.connect
        injected = True
