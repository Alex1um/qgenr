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
        payload = message.get_args()

        if len(payload) > 0:
            bytes_img = get_bytes(payload)

            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("invert", callback_data="invert=1"))

            await message.reply_photo(types.InputFile(bytes_img), caption=payload, reply_markup=kb)

    @dp.callback_query_handler()
    async def bt_handler(cq: types.callback_query.CallbackQuery):
        message = cq.message
        param, new_value = cq.data.split("=")
        command = message.reply_to_message.get_command(True)
        if command == "qr":
            code = get_bytes(message.get_args(), **{param: new_value})

            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("invert", callback_data=f"invert={'' if new_value else 1}"))

            await message.edit_media(types.InputMediaPhoto(types.InputFile(code)), kb)
        elif command == "ascii":
            code = get_ascii_qr(message.get_args(), **{param: new_value})

            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("invert", callback_data=f"invert={'' if new_value else 1}"))

            await message.edit_text(f"```\n{code}```", parse_mode="markdown", reply_markup=kb)

    @dp.message_handler(commands=["ascii"], regexp=r"^(\/ascii)(\s\S+)+(\s+)?$")
    async def on_ascii(message: Message) -> None:
        payload = message.get_args()

        if len(payload) > 0:
            code = get_ascii_qr(payload)

            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("invert", callback_data="invert=1"))

            await message.reply(f"```\n{code}```", parse_mode="markdown", reply_markup=kb)

    @dp.message_handler()
    async def on_message(message: Message) -> None:
        await message.reply(message.text)

    executor.start_polling(dp, skip_updates=True)
