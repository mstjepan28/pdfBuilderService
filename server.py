from PyPDF2 import PdfFileWriter, PdfFileReader, pdf
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

import pikepdf
import copy

# Load modckData thats used for testing
import json

file = open("mockData-10.json",)
mockData = json.load(file)
file.close()


app = None
routes = web.RouteTableDef()

@routes.post("/postTemplate")
async def postTemplate(request):
    data = await multipartFormReader(request) 
    pdfTemplate = readPdfTemplate(data["pdfTemplate"])
    
    print(type(pdfTemplate))
    
    for item in mockData:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4, bottomup=0)
        can.setFillColorRGB(0, 0, 0)
        
        for selection in data["selectionList"]:
            position = normalisePositionData(selection["positionData"], A4)
            can.drawString(position["x"], position["y"]+10, item.get(selection["variable"]))
            
        can.save()
        
        packet.seek(0)
        newPdf = PdfFileReader(packet)
                
        templatePage = getPageCopy(pdfTemplate.getPage(0), A4)
        templatePage.mergePage(newPdf.getPage(0))
        
        output = PdfFileWriter()
        output.addPage(templatePage)

        pdf_name = f"{item['first_name']}.pdf"

        outputStream = open("public/" + pdf_name, "wb")
        output.write(outputStream)
        outputStream.close()
    
    return web.json_response({})


# If this wasnt used, each drawing operation would overlay on top of eachother 
def getPageCopy(page, canvasSize):
    width, height = canvasSize
    
    pageCopy = pdf.PageObject.createBlankPage(None, width, height)
    pageCopy.mergePage(page)
    
    return pageCopy


# Read and decode parts of the multipart form
async def multipartFormReader(request):
    reader = aiohttp.MultipartReader.from_response(request)
    requestData = {}
    
    while True:
        # Get next form part
        part = await reader.next()
        
        if part is None:
            break
        
        # Get the JSON list of instructions on how to fill the PDF template
        elif part.headers['Content-Type'] == "application/octet-stream":
            byteArrayResult = await part.read(decode=True)
            jsonValue = byteArrayResult.decode('utf8').replace("'", '"')
            
            requestData["selectionList"] = json.loads(jsonValue)
            
        # Get the PDF template
        elif part.headers['Content-Type'] == "application/pdf":
            requestData["pdfTemplate"] = await part.read(decode=True)
                    
    return requestData


def readPdfTemplate(pdfTemplateByteArray):
    fileName = "temp.pdf"
    
    tempFile = open(fileName, "wb")
    tempFile.write(pdfTemplateByteArray)
    tempFile.close()
    
    pdf = pikepdf.open(fileName, allow_overwriting_input=True)
    pdf.save(fileName)
        
    return PdfFileReader(open(fileName, "rb")) 



# This PDF and the one on the frontend do not match in dimensions so the positionData is offset. 
#  To fix that the positionData is the percentage of the width/height of the PDF
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

if __name__ == "__main__":
    app = run()
    web.run_app(app, port=8080)