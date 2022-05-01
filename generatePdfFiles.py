from PyPDF2 import PdfFileWriter, PdfFileReader, pdf
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader

import io
import time

def fileGenerator(templateData, generateWithData):
  pdfTemplate = readPdfTemplate(templateData["pdfTemplate"])
  
  pdfSizeDict = templateData["pdfSize"]
  pdfSize = (pdfSizeDict["width"], pdfSizeDict["height"])
  
  for item in generateWithData:
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=pdfSize, bottomup=0)
    can.setFillColorRGB(0, 0, 0)
    
    for selection in templateData["selectionList"]:
      content = getContent(item, selection)
      position = normalizePositionData(selection["positionData"], pdfSize)
      
      if not content: 
        continue
      
      # Used for debugging - draw a rectangle around the area where the text will be drawn
      can.rect(position["x"], position["y"], position["width"], position["height"]) 
      
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

def readPdfTemplate(pdfTemplateByteArray):
  # No PDF template was sent
  if len(pdfTemplateByteArray) <= 4: 
    return PdfFileReader(open("fallback.pdf", "rb"))
  
  pdfDoc = io.BytesIO(pdfTemplateByteArray)
  return PdfFileReader(pdfDoc)


# This PDF and the one on the frontend do not match in dimensions so the positionData is offset. 
#  To fix that the positionData is the percentage of the width/height of the PDF
def normalizePositionData(positionData, canvasSize):
  width, height = canvasSize
  
  return {
    "x": positionData["x"] * width,
    "y": positionData["y"] * height,
    "width": positionData["width"] * width,
    "height": positionData["height"] * height,
  }


