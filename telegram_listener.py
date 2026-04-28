"""
telegram_listener.py
--------------------
Listens to a Telegram channel and fires a callback for each new message.

Uses Telethon (an async Telegram client library).
Your API credentials come from https://my.telegram.org.

The listener is intentionally thin — it doesn't know about trading.
It just receives messages and calls the on_signal callback you provide.
"""

import logging
from typing import Callable

from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat

logger = logging.getLogger(__name__)


class TelegramListener:
    def __init__(self, config: dict, on_message: Callable[[str], None]):
        """
        config: the "telegram" block from config.json
          api_id              : int
          api_hash            : str
          channel_username_or_id : str  (e.g. "t.me/+abc123" or "@channelname")

        on_message: callback that receives the raw message text string
        """
        tg = config["telegram"]
        self.api_id     = int(tg["api_id"])
        self.api_hash   = tg["api_hash"]
        self.channel    = tg["channel_username_or_id"]
        self.on_message = on_message

        # Session file stored alongside the script so Telethon remembers your login
        self.client = TelegramClient("mt5_copier_session", self.api_id, self.api_hash)

    async def start(self):
        """Connect, resolve the channel, and begin listening."""
        await self.client.start()
        logger.info("Telegram client started.")

        # Resolve the channel entity once upfront
        try:
            entity = await self.client.get_entity(self.channel)
            channel_name = getattr(entity, "title", self.channel)
            logger.info("Listening to channel: %s", channel_name)
        except Exception as exc:
            logger.error("Could not resolve channel '%s': %s", self.channel, exc)
            raise

        # Register the event handler for new messages in this channel
        @self.client.on(events.NewMessage(chats=entity))
        async def handler(event):
            text = event.message.text
            if not text:
                return  # ignore photo-only or sticker messages
            logger.debug("New message received:\n%s", text)
            try:
                self.on_message(text)
            except Exception as exc:
                logger.error("Error in on_message callback: %s", exc)

        logger.info("✅ Listening for signals. Press Ctrl+C to stop.")
        await self.client.run_until_disconnected()

    async def stop(self):
        await self.client.disconnect()
        logger.info("Telegram client disconnected.")
