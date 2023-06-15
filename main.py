import asyncio
import io
import os
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
_GEN_ARGS = frozenset({"color", "invert", "background", "border"})


def get_colors(color: str, background: str, invert: bool) -> tuple[str, str]:
    def is_hex_color_valid(color: str) -> bool:
        try:
            return len(color) == 7 and color[0] == "#" and int(color[1:], 16) is not None
        except Exception:
            return False

    if not is_hex_color_valid(color):
        color = 0x000000
    else:
        color = int(color[1:], 16)
    if not is_hex_color_valid(background):
        background = 0xffffff
    else:
        background = int(background[1:], 16)
    if invert:
        color = 0xffffff - color
        background = 0xffffff - background
    return f"#{hex(color)[2:]:>0{6}}", f"#{hex(background)[2:]:>0{6}}"


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def get_ascii_qr(data: str, border=None, invert=False, color="#000000", background="#ffffff", **kwargs) -> str:
    qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage, border=int(border or 0))
    qr.add_data(data)
    s = io.StringIO()

    # color, background = map(hex_to_rgb, get_colors(color, background, invert))
    # s.write(f"\033[38;2;{color[0]};{color[1]};{color[2]}m")
    # s.write(f"\033[48;2;{background[0]};{background[1]};{background[2]}m")
    qr.print_ascii(s, invert=invert)
    s.seek(0)
    return s.read()


def get_svg_qr(data: str, border=None, invert=False, background="#ffffff", color="#000000", **kwargs) -> str:

    qr = qrcode.QRCode(
        image_factory=qrcode.image.svg.SvgPathFillImage,
        border=int(border or 4)
    )
    qr.add_data(data)
    qr.make(fit=True)
    color, background = get_colors(color, background, invert)
    qr.image_factory.QR_PATH_STYLE = {
        "fill": color,
        "fill-opacity": "1",
        "fill-rule": "nonzero",
        "stroke": "none",
    }
    qr.image_factory.background = background
    # style = """
    # width: 100%;
    # height:100%;
    # """
    # if invert:
    #     style += "filter: invert(100%);"
    img = qr.make_image(
        # attrib={"style": style},
        )

    return img.to_string(encoding="unicode")


def get_bytes(data: str, border=None, invert=False, color="#000000", background="#ffffff", **kwargs) -> BytesIO:
    qr = qrcode.QRCode(border=int(border or 4))
    qr.add_data(data)
    qr.make(fit=True)

    # img = qr.make_image(fill_color=(255, 255, 255), back_color=(0, 0, 0))
    img = qr.make_image()
    png_img: png.Writer = img.get_image()

    png_img.color_type = 3

    color, background = get_colors(color, background, invert)
    color, background = map(hex_to_rgb, (color, background))
    png_img.palette = (color, background)

    # if invert:
    #     png_img.palette = [[255, 255, 255], [0, 0, 0]]

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
    kwargs = {k:v for k, v in query.items() if k in _GEN_ARGS}
    query = {k:v for k, v in query.items() if k not in _GEN_ARGS}
    return kwargs, query


def create_app(stop=False):
    app = web.Application()
    routes = web.RouteTableDef()

    @routes.get(r"/qr/png/{payload:.*}")
    @routes.get(r'/qr/img/{payload:.*}')
    async def on_img(req: web.Request):
        kwargs, query = get_kwargs(req.query)
        payload = str(yarl.URL(req.match_info['payload']).with_query(query))
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
        return get_response(payload, "text/plain", **kwargs)

    @routes.get(r'/qr/ascii')
    async def on_ascii_query(req: web.Request):
        payload = req.query.get("data", "") or req.query.get("qr", "")
        return get_response(payload, "text/plain", **get_kwargs(req.query))

    @routes.get(r'/qr/svg/{payload:.*}')
    async def on_svg(req: web.Request):
        kwargs, query = get_kwargs(req.query)
        payload = str(yarl.URL(req.match_info['payload']).with_query(query))
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
