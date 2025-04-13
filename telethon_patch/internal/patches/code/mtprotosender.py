from telethon import helpers
from telethon.network import MTProtoSender as MTProtoSenderOriginal


class MTProtoSender(MTProtoSenderOriginal):
    async def _disconnect(self, error=None):
        if self._connection is None:
            self._log.info('Not disconnecting (already have no connection)')
            return

        self._log.info('Disconnecting from %s...', self._connection)
        self._user_connected = False
        try:
            self._log.debug('Closing current connection...')
            await self._connection.disconnect()
        finally:
            self._log.debug('Cancelling %d pending message(s)...', len(self._pending_state))
            for state in self._pending_state.values():
                if error and not state.future.done():
                    state.future.set_result(error)
                else:
                    state.future.cancel()

            self._pending_state.clear()
            await helpers._cancel(
                self._log,
                send_loop_handle=self._send_loop_handle,
                recv_loop_handle=self._recv_loop_handle
            )

            self._log.info('Disconnection from %s complete!', self._connection)
            self._connection = None

        if self._disconnected and not self._disconnected.done():
            self._disconnected.set_result(error if error else None)
