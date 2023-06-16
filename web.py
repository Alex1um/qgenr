from aiohttp import web
import yarl
import asyncio
import os
from base import *
from base import _GEN_ARGS
from aiohttp_swagger3 import SwaggerDocs, SwaggerInfo, SwaggerUiSettings


def get_response(payload: str, content_type: str, **kwargs) -> web.Response:
    if payload:
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
    return web.HTTPBadRequest()


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
        """
        ---
        summary: Generate svg QR code with query params
        tags:
          - qr
          - png
        parameters:
          - name: payload
            in: path
            required: true
            description: QR code data
            schema:
              type: string
              format: string
          - name: color
            in: query
            description: QR code color - hex format
            schema:
              type: string
              pattern: '^#[0-9a-f]{6}$'
            examples:
              --:
                value: ''
              red:
                value: '#ff0000'
              green:
                value: '#00ff00'
              blue:
                value: '#0000ff'
          - name: background
            in: query
            description: QR code background color - hex format
            schema:
              type: string
              pattern: '^#[0-9a-f]{6}$'
            examples:
              --:
                value: ''
              red:
                value: '#ff0000'
              green:
                value: '#00ff00'
              blue:
                value: '#0000ff'
          - name: border
            in: query
            description: QR code border
            schema:
              type: integer
              minimum: 1
          - name: invert
            in: query
            description: QR code inversion
            schema:
              type: boolean
        responses:
          '200':
            description: QR code with given data and params
          '500':
            description: Unexpected server error - wrong params
          '400':
            description: Wrong params
        """
        kwargs, query = get_kwargs(req.query)
        payload = str(yarl.URL(req.match_info['payload']).update_query(query))
        return get_response(payload, "image/png", **kwargs)

    @routes.get(r'/qr/png')
    @routes.get(r'/qr/img')
    async def on_img_query(req: web.Request):
        """
        ---
        summary: Generate svg QR code with query params
        tags:
          - qr
          - png
        parameters:
          - name: data
            in: query
            required: true
            description: QR code data
            schema:
              type: string
              format: string
          - name: color
            in: query
            description: QR code color - hex format
            schema:
              type: string
              pattern: '^#[0-9a-f]{6}$'
            examples:
              --:
                value: ''
              red:
                value: '#ff0000'
              green:
                value: '#00ff00'
              blue:
                value: '#0000ff'
          - name: background
            in: query
            description: QR code background color - hex format
            schema:
              type: string
              pattern: '^#[0-9a-f]{6}$'
            examples:
              --:
                value: ''
              red:
                value: '#ff0000'
              green:
                value: '#00ff00'
              blue:
                value: '#0000ff'
          - name: border
            in: query
            description: QR code border
            schema:
              type: integer
              minimum: 1
          - name: invert
            in: query
            description: QR code inversion
            schema:
              type: boolean
        responses:
          '200':
            description: QR code with given data and params
          '500':
            description: Unexpected server error - wrong params
          '400':
            description: Wrong params
        """
        payload = req.query.get("data", "") or req.query.get("qr", "")
        return get_response(payload, "image/png", **get_kwargs(req.query)[0])

    @routes.get(r'/qr/ascii/{payload:.*}')
    async def on_ascii(req: web.Request):
        """
        ---
        summary: Generate svg QR code with query params
        tags:
          - qr
          - ascii
        parameters:
          - name: payload
            in: path
            required: true
            description: QR code data
            schema:
              type: string
              format: string
          - name: color
            in: query
            description: QR code color - hex format
            schema:
              type: string
              pattern: '^#[0-9a-f]{6}$'
            examples:
              --:
                value: ''
              red:
                value: '#ff0000'
              green:
                value: '#00ff00'
              blue:
                value: '#0000ff'
          - name: background
            in: query
            description: QR code background color - hex format
            schema:
              type: string
              pattern: '^#[0-9a-f]{6}$'
            examples:
              --:
                value: ''
              red:
                value: '#ff0000'
              green:
                value: '#00ff00'
              blue:
                value: '#0000ff'
          - name: border
            in: query
            description: QR code border
            schema:
              type: integer
              minimum: 1
          - name: invert
            in: query
            description: QR code inversion
            schema:
              type: boolean
        responses:
          '200':
            description: QR code with given data and params
          '500':
            description: Unexpected server error - wrong params
          '400':
            description: Wrong params
        """
        kwargs, query = get_kwargs(req.query)
        payload = str(yarl.URL(req.match_info['payload']).update_query(query))
        return get_response(payload, "text/plain", **kwargs)

    @routes.get(r'/qr/ascii')
    async def on_ascii_query(req: web.Request):
        """
        ---
        summary: Generate svg QR code with query params
        tags:
          - qr
          - ascii
        parameters:
          - name: data
            in: query
            required: true
            description: QR code data
            schema:
              type: string
              format: string
          - name: color
            in: query
            description: QR code color - hex format
            schema:
              type: string
              pattern: '^#[0-9a-f]{6}$'
            examples:
              --:
                value: ''
              red:
                value: '#ff0000'
              green:
                value: '#00ff00'
              blue:
                value: '#0000ff'
          - name: background
            in: query
            description: QR code background color - hex format
            schema:
              type: string
              pattern: '^#[0-9a-f]{6}$'
            examples:
              --:
                value: ''
              red:
                value: '#ff0000'
              green:
                value: '#00ff00'
              blue:
                value: '#0000ff'
          - name: border
            in: query
            description: QR code border
            schema:
              type: integer
              minimum: 1
          - name: invert
            in: query
            description: QR code inversion
            schema:
              type: boolean
        responses:
          '200':
            description: QR code with given data and params
          '500':
            description: Unexpected server error - wrong params
          '400':
            description: Wrong params
        """
        payload = req.query.get("data", "") or req.query.get("qr", "")
        return get_response(payload, "text/plain", **get_kwargs(req.query))

    @routes.get(r'/qr/svg/{payload:.*}')
    async def on_svg(req: web.Request):
        """
        ---
        summary: Generate svg QR code with query params
        tags:
          - qr
          - svg
        parameters:
          - name: payload
            in: path
            required: true
            description: QR code data
            schema:
              type: string
              format: string
          - name: color
            in: query
            description: QR code color - hex format
            schema:
              type: string
              pattern: '^#[0-9a-f]{6}$'
            examples:
              --:
                value: ''
              red:
                value: '#ff0000'
              green:
                value: '#00ff00'
              blue:
                value: '#0000ff'
          - name: background
            in: query
            description: QR code background color - hex format
            schema:
              type: string
              pattern: '^#[0-9a-f]{6}$'
            examples:
              --:
                value: ''
              red:
                value: '#ff0000'
              green:
                value: '#00ff00'
              blue:
                value: '#0000ff'
          - name: border
            in: query
            description: QR code border
            schema:
              type: integer
              minimum: 1
          - name: invert
            in: query
            description: QR code inversion
            schema:
              type: boolean
        responses:
          '200':
            description: QR code with given data and params
          '500':
            description: Unexpected server error - wrong params
          '400':
            description: Wrong params
        """
        kwargs, query = get_kwargs(req.query)
        payload = str(yarl.URL(req.match_info['payload']).update_query(query))
        return get_response(payload, "image/svg+xml", **kwargs)

    @routes.get(r'/qr/svg')
    async def on_svg_query(req: web.Request):
        """
        ---
        summary: Generate svg QR code with query params
        tags:
          - qr
          - svg
        parameters:
          - name: data
            in: query
            required: true
            description: QR code data
            schema:
              type: string
              format: string
          - name: color
            in: query
            description: QR code color - hex format
            schema:
              type: string
              pattern: '^#[0-9a-f]{6}$'
            examples:
              --:
                value: ''
              red:
                value: '#ff0000'
              green:
                value: '#00ff00'
              blue:
                value: '#0000ff'
          - name: background
            in: query
            description: QR code background color - hex format
            schema:
              type: string
              pattern: '^#[0-9a-f]{6}$'
            examples:
              --:
                value: ''
              red:
                value: '#ff0000'
              green:
                value: '#00ff00'
              blue:
                value: '#0000ff'
          - name: border
            in: query
            description: QR code border
            schema:
              type: integer
              minimum: 1
          - name: invert
            in: query
            description: QR code inversion
            schema:
              type: boolean
        responses:
          '200':
            description: QR code with given data and params
          '500':
            description: Unexpected server error - wrong params
          '400':
            description: Wrong params
        """
        payload = req.query.get("data", "") or req.query.get("qr", "")
        return get_response(payload, "image/svg+xml", **get_kwargs(req.query)[0])

    @routes.get(r'/qr')
    async def on_qr(req: web.Request) -> web.Response:
        """
        ---
        summary: Generate QR code with query params
        tags:
          - qr
          - svg
          - png
          - ascii
        parameters:
          - name: data
            in: query
            required: true
            description: QR code data
            schema:
              type: string
              format: string
          - name: type
            in: query
            description: QR code type
            schema:
              type: string
              default: png
              enum: [svg, img, png, ascii]
          - name: color
            in: query
            description: QR code color - hex format
            schema:
              type: string
              pattern: '^#[0-9a-f]{6}$'
            examples:
              --:
                value: ''
              red:
                value: '#ff0000'
              green:
                value: '#00ff00'
              blue:
                value: '#0000ff'
          - name: background
            in: query
            description: QR code background color - hex format
            schema:
              type: string
              pattern: '^#[0-9a-f]{6}$'
            examples:
              --:
                value: ''
              red:
                value: '#ff0000'
              green:
                value: '#00ff00'
              blue:
                value: '#0000ff'
          - name: border
            in: query
            description: QR code border
            schema:
              type: integer
              minimum: 1
          - name: invert
            in: query
            description: QR code inversion
            schema:
              type: boolean
        responses:
          '200':
            description: QR code with given data and params
          '500':
            description: Unexpected server error - wrong params
          '400':
            description: Wrong params
        """
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
        return get_response(payload, content_type, **get_kwargs(req.query)[0])

    @routes.get("/")
    async def on_main(req: web.Request):
        """
        ---
        summary: Main page
        tags:
          - main
        responses:
          '200':
            description: Ok
        """
        return web.HTTPOk()

    swagger = SwaggerDocs(
        app,
        swagger_ui_settings=SwaggerUiSettings(path="/api"),
        validate=False,
    )
    swagger.add_routes(routes)
    runner = web.AppRunner(app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, "0.0.0.0", os.getenv("PORT", "8080"))
    loop.run_until_complete(site.start())
    if stop:
        loop.run_forever()
