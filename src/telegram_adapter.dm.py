import asyncio
import datetime
import logging
import pathlib
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import message_bus as mb
from swarm_config import load_config, SwarmConfig

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


class Handler:

  def __init__(self, config: SwarmConfig, message_bus: mb.MessageBus) -> None:
    assert config.telegram
    self._config = config
    self._message_bus = message_bus

  async def start(self, update: Update,
                  context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    await update.message.reply_text("I'm awake!")

  async def echo(self, update: Update,
                 context: ContextTypes.DEFAULT_TYPE) -> None:
    """Receives a message from Telegram and inserts it to the message bus.

    If the update is a response to a previous message, looks up the previous
    message in the message bus. If the previous message is found, the new row
    will set `target_agent` to `original_message.source_agent` and propagate
    `conversation_id`.

    `source_agent` is set to the value in `END_USER_AGENT`.

    A response is sent to the chat and logged: f"Message received ({id=})"
    """
    assert update.effective_chat  # for telegram_chat_id.
    raise NotImplementedError()  # {{🍄 write message to bus and respond}}

  async def _send_outgoing_messages(self) -> None:
    """Calls wait_for_outgoing_messages and dispatches messages to the user.

    For each message received, calls `self._app.bot.send_message` and
    `set_telegram_message_id` (based on resulting outgoing message).

    {{🦔 The content of the outgoing messages starts with the source agent.}}
    """
    raise NotImplementedError()  # {{🍄 read new outgoing messages}}

  async def run(self) -> None:
    await self._message_bus.open()
    assert self._config.telegram
    assert self._config.telegram.token
    self._app = Application.builder().token(self._config.telegram.token).build()
    self._app.add_handler(
        CommandHandler(
            "start",
            self.start,
            filters=filters.User(self._config.telegram.authorized_users)))
    self._app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND
            & filters.User(self._config.telegram.authorized_users), self.echo))

    asyncio.create_task(self._send_outgoing_messages())

    async with self._app:
      await self._app.initialize()
      await self._app.start()
      assert self._app.updater
      await self._app.updater.start_polling()
      print("Bot is polling... Press Ctrl+C to stop.")
      while True:
        await asyncio.sleep(1)


async def main() -> None:
  config = await load_config(pathlib.Path('swarm/config.json'))
  assert config.telegram
  await Handler(config, mb.MessageBus(config.message_bus_path)).run()


if __name__ == '__main__':
  asyncio.run(main())
