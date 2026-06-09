from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup


@dataclass(frozen=True)
class TelegramNotifier:
    bot: Bot
    chat_id: str

    async def send_text(self, text: str) -> None:
        await self.bot.send_message(chat_id=self.chat_id, text=text)

    async def send_alert_with_camera_button(self, text: str) -> None:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Sim", callback_data="cam:yes"),
                    InlineKeyboardButton("Nao", callback_data="cam:no"),
                ]
            ]
        )
        await self.bot.send_message(chat_id=self.chat_id, text=text, reply_markup=keyboard)

    async def send_photo(self, photo_bytes: bytes, caption: str | None = None) -> None:
        photo = BytesIO(photo_bytes)
        photo.name = "camera-frame.jpg"
        await self.bot.send_photo(chat_id=self.chat_id, photo=photo, caption=caption)