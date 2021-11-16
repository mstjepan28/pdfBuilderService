from PyPDF2 import PdfFileWriter, PdfFileReader
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import aiohttp
from aiohttp import web
import aiohttp_cors
from urllib import parse
import base64
from hashlib import blake2b

import json

file = open("mockData-10.json",)
mockData = json.load(file)
file.close()

app = None
routes = web.RouteTableDef()


@routes.post("/postTemplate")
async def postTemplate(request):
    data = await request.json()
    #############################################
    #############################################
    
    width, height = A4
    
    packet = io.BytesIO()
    
    can = canvas.Canvas(packet, pagesize=A4, bottomup=0)
    can.setFillColorRGB(0, 0, 0)
    
    for item in mockData:
        for selection in data["selectionList"]:
            position = normalisePositionData(selection["positionData"], A4)
            can.drawString(position["x"], position["y"]+10, item.get(selection["variable"]))
            
        #return
        can.save()
        
        packet.seek(0)
        new_pdf = PdfFileReader(packet)

        existing_pdf = PdfFileReader(open("blankTemplate.pdf", "rb"))
        print(existing_pdf.getPage(0).mediaBox)
        output = PdfFileWriter()

        page = existing_pdf.getPage(0)
        page.mergePage(new_pdf.getPage(0))
        output.addPage(page)

        pdf_name = f"{item['first_name']}.pdf"

        outputStream = open("public/" + pdf_name, "wb")
        output.write(outputStream)
        outputStream.close()

        return web.json_response({"attachment_url": "http://0.0.0.0:8080/public/" + pdf_name})

def normalisePositionData(positionData, canvasSize):
    width, height = canvasSize
    
    return {
        "x": positionData["x"] * width,
        "y": positionData["y"] * height,
        "width": positionData["width"] * width,
        "height": positionData["height"] * height,
    }

if not os.path.exists("public"):
    os.makedirs("public")

def run():
    global app

    app = web.Application()
    app.add_routes(routes)
    app.add_routes([web.static("/public", "./public")])

    cors = aiohttp_cors.setup( app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*",
        )},
    )

    for route in list(app.router.routes()):
        cors.add(route)

    return app


async def serve():
    return run()

if __name__ == "__main__":
    app = run()
    web.run_app(app, port=8080)