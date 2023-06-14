import asyncio
import io
import os
import html
from io import BytesIO

import png
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import Message
import logging
from aiohttp import web
import qrcode
import qrcode.image.svg
import qrcode.image.styles.moduledrawers.svg
import qrcode.image.styles.moduledrawers.base
import qrcode.image.styles.colormasks
import qrcode.image.base
import qrcode.image.pure
import yarl

logging.basicConfig(level=logging.INFO)


def get_ascii_qr(data: str, border=None, invert=False, **kwargs) -> str:
    qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage, border=int(border or 0))
    qr.add_data(data)
    s = io.StringIO()
    qr.print_ascii(s, invert=invert)
    s.seek(0)
    return s.read()


def get_svg_qr(data: str, border=None, invert=False, **kwargs) -> str:
    qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage, border=int(border or 4))
    qr.add_data(data)
    qr.make(fit=True)
    style = """
    width: 100%;
    height:100%;
    """
    if invert:
        style += "filter: invert(100%);"
    img = qr.make_image(
        attrib={"style": style},
        )

    return img.to_string(encoding="unicode")


def get_bytes(data: str, border=None, invert=False, **kwargs) -> BytesIO:
    qr = qrcode.QRCode(border=int(border or 4))
    qr.add_data(data)
    qr.make(fit=True)

    # img = qr.make_image(fill_color=(255, 255, 255), back_color=(0, 0, 0))
    img = qr.make_image()
    png_img: png.Writer = img.get_image()

    if invert:
        png_img.color_type = 3
        png_img.palette = [[255, 255, 255], [0, 0, 0]]

    bytes = io.BytesIO()
    img.save(bytes)
    bytes.seek(0)
    return bytes


def get_response(payload: str, content_type: str, **kwargs) -> web.Response:
    if not payload:
        web.HTTPBadRequest()
    response = web.Response(charset="utf-8", content_type=content_type,
                            headers={"Access-Control-Allow-Origin": "*"})
    match content_type:
        case "image/png":
            response.body = get_bytes(payload, **kwargs)
        case "text/plain":
            response.body = get_ascii_qr(payload, **kwargs)
        case "image/svg+xml":
            response.body = get_svg_qr(payload, **kwargs)
            # body=f"<pre align='center' style='line-height: 1em;'>{get_ascii_qr(payload)}</pre>",
    return response


def get_kwargs(query: web.Request.query) -> (dict, dict):
    kwargs = {k:v for k, v in query.items() if k in {"invert", "border"}}
    query = {k:v for k, v in query.items() if k not in {"invert", "border"}}
    return kwargs, query


def create_app(stop=False):
    app = web.Application()
    routes = web.RouteTableDef()

    @routes.get(r"/qr/png/{payload:.*}")
    @routes.get(r'/qr/img/{payload:.*}')
    async def on_img(req: web.Request):
        kwargs, query = get_kwargs(req.query)
        payload = str(yarl.URL(req.match_info['payload']).with_query(query))
        payload = html.unescape(payload)
        return get_response(payload, "image/png", **kwargs)

    @routes.get(r'/qr/png')
    @routes.get(r'/qr/img')
    async def on_img(req: web.Request):
        payload = req.query.get("data", "") or req.query.get("qr", "")
        return get_response(payload, "image/png", **get_kwargs(req.query)[0])

    @routes.get(r'/qr/ascii/{payload:.*}')
    async def on_ascii(req: web.Request):
        kwargs, query = get_kwargs(req.query)
        payload = str(yarl.URL(req.match_info['payload']).with_query(query))
        payload = html.unescape(payload)
        return get_response(payload, "text/plain", **kwargs)

    @routes.get(r'/qr/ascii')
    async def on_ascii_query(req: web.Request):
        payload = req.query.get("data", "") or req.query.get("qr", "")
        return get_response(payload, "text/plain", **get_kwargs(req.query))

    @routes.get(r'/qr/svg/{payload:.*}')
    async def on_svg(req: web.Request):
        kwargs, query = get_kwargs(req.query)
        payload = str(yarl.URL(req.match_info['payload']).with_query(query))
        payload = html.unescape(payload)
        return get_response(payload, "image/svg+xml", **kwargs)

    @routes.get(r'/qr/svg')
    async def on_svg_query(req: web.Request):
        payload = req.query.get("data", "") or req.query.get("qr", "")
        return get_response(payload, "image/svg+xml", **get_kwargs(req.query)[0])

    @routes.get(r'/qr')
    async def on_qr(req: web.Request):
        payload = req.query.get("data", "") or req.query.get("qr", "")
        type = req.query.get("type", "png")
        match type:
            case "svg":
                content_type = "image/svg+xml"
            case "ascii":
                content_type = "text/plain"
            case "png" | "img":
                content_type = "image/png"
            case _:
                return web.HTTPBadRequest()
        return get_response(payload, content_type, **get_kwargs(req.query))

    @routes.get("/")
    async def on_main(req: web.Request):
        return web.HTTPOk()

    app.router.add_routes(routes)
    runner = web.AppRunner(app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, "0.0.0.0", os.getenv("PORT", "8080"))
    loop.run_until_complete(site.start())
    logging.log(logging.INFO, "Started http")
    if stop:
        loop.run_forever()


def create_bot():
    TOKEN = os.getenv("TOKEN")

    bot = Bot(TOKEN)

    dp = Dispatcher(bot)

    @dp.message_handler(commands=["qr"], regexp=r"^(\/qr)(\s\S+)+(\s+)?$")
    async def on_qr(message: Message) -> None:
        payload = " ".join(message.text.split()[1:]).strip()

        if len(payload) > 0:
            bytes_img = get_bytes(payload)

            media = types.MediaGroup()
            media.attach_photo(types.InputFile(bytes_img), payload)
            await message.reply_media_group(media)

    @dp.message_handler(commands=["ascii"], regexp=r"^(\/ascii)(\s\S+)+(\s+)?$")
    async def on_test(message: Message) -> None:
        payload = " ".join(message.text.split()[1:]).strip()

        if len(payload) > 0:
            await message.reply(f"```\n{get_ascii_qr(payload)}```", parse_mode="markdown")

    @dp.message_handler()
    async def on_message(message: Message) -> None:
        await message.reply(message.text)

    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    create_app()
    create_bot()
