import os
import shlex
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import Message
from base import *


def create_bot():
    TOKEN = os.getenv("TOKEN")

    bot = Bot(TOKEN)

    dp = Dispatcher(bot)

    @dp.message_handler(commands=["qr"], regexp=r"^(\/qr)(\s\S+)+(\s+)?$")
    async def on_qr(message: Message) -> None:
        args = shlex.split(message.get_args().strip())
        payload = args[-1]

        if len(payload) > 0:
            if len(args) > 2:
                color, background = get_colors(args[0], args[1], False)
                bytes_img = get_bytes(payload, color=color, background=background)
            else:
                bytes_img = get_bytes(payload)

            media = types.MediaGroup()
            media.attach_photo(types.InputFile(bytes_img), payload)
            await message.reply_media_group(media)

    @dp.message_handler(commands=["ascii"], regexp=r"^(\/ascii)(\s\S+)+(\s+)?$")
    async def on_test(message: Message) -> None:
        args = shlex.split(message.get_args().strip())
        payload = args[-1]

        if len(payload) > 0:
            if len(args) > 2:
                color, background = get_colors(args[0], args[1], False)
                code = get_ascii_qr(payload, color=color, background=background)
            else:
                code = get_ascii_qr(payload)
            await message.reply(f"```\n{code}```", parse_mode="markdown")

    @dp.message_handler()
    async def on_message(message: Message) -> None:
        await message.reply(message.text)

    executor.start_polling(dp, skip_updates=True)
