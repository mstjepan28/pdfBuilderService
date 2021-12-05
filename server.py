import aiohttp
from aiohttp import web
import aiohttp_cors

import io
import os
import json
import base64
import pikepdf
import fitz

from PyPDF2 import PdfFileWriter, PdfFileReader, pdf
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader


# Load modckData thats used for testing
file = open("mockData-10.json",)
mockData = json.load(file)
file.close()

app = None
routes = web.RouteTableDef()

@routes.get("/variables")
async def getValiables(request):
    variables = list(mockData[0].keys())
    
    return web.json_response({
        "variables": variables 
    })

@routes.post("/convertPdfToImg")
async def convertPdfToImg(request):
    data = await multipartFormReader(request)
    pdfBytesArray = data["pdfTemplate"]
    
    file = open("temp.pdf", "wb")
    file.write(pdfBytesArray)
    file.close()
    
    pdfDoc = fitz.open("temp.pdf")
    pdfPage = pdfDoc.load_page(0)
    image = pdfPage.get_pixmap()
    image.save("public/images/output.png")
    
    return web.json_response({
        "attachment_url": "http://localhost:8080/public/images/output.png"
    })
   
@routes.post("/postTemplate")
async def postTemplate(request):
    receivedData = await multipartFormReader(request) 
    pdfTemplate = readPdfTemplate(receivedData["pdfTemplate"])
    
    pdfSizeDict = receivedData["pdfSize"]
    
    pdfSize = (pdfSizeDict["width"], pdfSizeDict["height"])
    
    for item in mockData:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=pdfSize, bottomup=0)
        can.setFillColorRGB(0, 0, 0)
        
        for selection in receivedData["selectionList"]:
            content = getContent(item, selection)
            position = normalisePositionData(selection["positionData"], pdfSize)
            
            if not content: 
                continue
            
            can.rect(position["x"], position["y"], position["width"], position["height"]) # ----------------- DEBUGING -----------------
            
            if(selection["type"] == "singlelineText"):
                handleText(can, position, content)
            elif(selection["type"] == "paragraph"):
                handleParagraph(can, position, content)
            elif(selection["type"] == "image"):
                handleImage(can, position, content)
            
        can.save()
        
        packet.seek(0)
        newPdf = PdfFileReader(packet)
                
        templatePage = getPageCopy(pdfTemplate.getPage(0), pdfSize)
        templatePage.mergePage(newPdf.getPage(0))
        
        output = PdfFileWriter()
        output.addPage(templatePage)

        pdf_name = f"{item['student']}.pdf"

        outputStream = open("public/" + pdf_name, "wb")
        output.write(outputStream)
        outputStream.close()
    
    return web.json_response({})


# Return static content or content based on the given variable if no static
#   content is given
def getContent(item, selection):
    if selection["staticContent"]:
        content = selection["staticContent"]
    else:
        content = item.get(selection["variable"])
    
    return False if content == None else str(content)


# Draw single line text on the canvas
def handleText(can, position, content):
    can.drawString(position["x"], position["y"] + 10, content)


# Draw a paragraph and make sure it breaks/aligns correctly
def handleParagraph(can, position, content):
    paragraphContent = Paragraph(content)
    xCord, yCord = paragraphContent.wrap(position["width"], position["height"])
    
    yOffset = yCord - 16
    
    paragraphContent.drawOn(can, position["x"], position["y"] - yOffset)

# Read the image as a URL or a base64 and draw it on the canvas. Because of the 
#   bottomUp=0 the images get drawn upside down so we fix that
def handleImage(can, position, content):
    image = ImageReader(content)
    
    can.saveState()
    
    can.translate(position["x"], position["y"])
    can.scale(1,-1)
    
    can.drawImage(image, 0, 0, position["width"], -position["height"], mask='auto')
    
    can.restoreState()


# Used to prevent drawing operations from overlay on top of eachother 
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
        elif part.headers['Content-Type'] == "application/json":
            byteArrayResult = await part.read(decode=True)
            
            jsonValue = byteArrayResult.decode('utf8').replace("'", '"')
            jsonData = json.loads(jsonValue)
            
            formPartName = part.headers["Content-Disposition"].split(" ")[2]
            
            if formPartName == 'filename="selectionList"':
                requestData["selectionList"] = jsonData
            elif formPartName == 'filename="pdfDimensions"':
                requestData["pdfSize"] = jsonData
                
        # Get the PDF template
        elif part.headers['Content-Type'] == "application/pdf":
            requestData["pdfTemplate"] = await part.read(decode=True)
                    
    return requestData


def readPdfTemplate(pdfTemplateByteArray):
    # No PDF template was sent
    if len(pdfTemplateByteArray) <= 4: 
        return PdfFileReader(open("fallback.pdf", "rb"))    
    
    pdfDoc = io.BytesIO(pdfTemplateByteArray)    
    return PdfFileReader(pdfDoc)


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