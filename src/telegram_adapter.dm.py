import asyncio
import logging
import pathlib
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from message_bus import MessageBus, Message as BusMessage, MessageId, SenderName, SessionId
from swarm_config import load_config, SwarmConfig

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


class Handler:

  def __init__(self, config: SwarmConfig, message_bus: MessageBus) -> None:
    assert config.telegram
    self._chat_id: int | None = None
    self._config = config
    self._message_bus = message_bus

  async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    assert update.message
    await update.message.reply_text(
        "I'm awake! Send me any message and I'll repeat it.")

  async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives a message from Telegram.

    The message is written to the bus, with the `config.telegram.consumer` value
    as the recipient.

    A response is sent to the chat and logged: f"Message received ({id=})"
    """
    assert update.effective_chat
    self._chat_id = update.effective_chat.id
    raise NotImplementedError()  # {{🍄 write message to bus and respond}}

  async def _read_message_bus(self):
    """Calls wait_for_new_messages and dispatches messages to the user.

    If self._chat_id is not set, polls doing nothing until it gets set.

    When it receives messages, calls self._app.bot.send_message to dispatch
    them to self._chat_id.

    Calls `mark_message_as_seen` on all messages processed.

    Only receives messages with recipient set to
    `config.telegram.end_user_identity.`
    """
    raise NotImplementedError()  # {{🍄 read message bus}}

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

    asyncio.create_task(self._read_message_bus())

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
  await Handler(config, MessageBus(config.message_bus_path)).run()


if __name__ == '__main__':
  asyncio.run(main())
