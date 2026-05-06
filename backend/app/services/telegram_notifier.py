from dataclasses import dataclass
from telegram import Bot


@dataclass(frozen=True)
class TelegramNotifier:
    bot: Bot
    chat_id: str

    async def send_text(self, text: str) -> None:
        await self.bot.send_message(chat_id=self.chat_id, text=text)