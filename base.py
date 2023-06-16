import io
from io import BytesIO
import png
import qrcode
import qrcode.image.svg
import qrcode.image.styles.moduledrawers.svg
import qrcode.image.styles.moduledrawers.base
import qrcode.image.styles.colormasks
import qrcode.image.base
import qrcode.image.pure


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
    if bool(invert):
        color = 0xffffff - color
        background = 0xffffff - background
    return f"#{hex(color)[2:]:>0{6}}", f"#{hex(background)[2:]:>0{6}}"


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def get_ascii_qr(data: str, border=None, invert=False, **kwargs) -> str:
    qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage, border=int(border or 0))
    qr.add_data(data)
    s = io.StringIO()

    # color, background = map(hex_to_rgb, get_colors(color, background, invert))
    # s.write(f"\033[38;2;{color[0]};{color[1]};{color[2]}m")
    # s.write(f"\033[48;2;{background[0]};{background[1]};{background[2]}m")
    qr.print_ascii(s, invert=bool(invert))
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

    bytes = io.BytesIO()
    img.save(bytes)
    bytes.seek(0)
    return bytes

