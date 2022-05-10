import aiohttp
from aiohttp import web
import aiohttp_cors

import os
import json
import base64
import pikepdf
import fitz
import uuid
import time
from datetime import datetime

import database
from generatePdfFiles import fileGenerator

app = None
port = 5500

database.setupDatabase()
routes = web.RouteTableDef()

# TODO: remove this eventually
def getTestingData():
  with open("mockData-10.json", 'r') as jsonFile:
    jsonData = json.load(jsonFile)
    return jsonData

@routes.post("/postTemplate")
async def postTemplate(request):
  templateData = await multipartFormReader(request)
  generateWithData = getTestingData()
  
  fileGenerator(templateData, generateWithData)
  
  return web.json_response({})


@routes.get("/previewData")
async def previewData(request):
  template = getTestingData()[0]
  return web.json_response(template)

###############################################################################

@routes.post("/templates")
async def templates(request):
  data = await multipartFormReader(request)
  template = data["template"]
  
  template["baseTemplateId"] = f"{template['id']}.pdf" if data["pdfTemplate"] else None
  template["createdBy"] = "TODO: get user here"
  template["createdAt"] = str(datetime.now())
  template["updatedAt"] = str(datetime.now())
  
  database.addTemplate(template)
  
  savePdfTemplateFile(data["pdfTemplate"], f"{template['id']}.pdf")
  
  return web.json_response(template)


@routes.put("/templates")
async def templates(request):
  data = await multipartFormReader(request)
  template = data["template"]
  
  template["updatedAt"] = str(time.time() * 1000)
  
  database.updateTemplate(template["id"], template)
  
  return web.json_response(template)


@routes.get("/templates")
async def templates(request):
  templateId = request.rel_url.query.get("id")
  
  if templateId:
    template = database.getTemplateById(templateId)
    return web.json_response(template)
  else:
    templates = database.getAllTemplates()
    return web.json_response(templates)


@routes.delete("/templates")
async def deleteTemplate(request):
  templateId = request.rel_url.query.get("id")
  success = database.deleteTemplate(templateId)
  
  return web.json_response({"success": success})

###############################################################################

@routes.get("/generateUUID")
async def generateUUID(request):
  return web.json_response({
    "id": str(uuid.uuid4())
  })


@routes.post("/convertPdfToImg")
async def convertPdfToImg(request):
  data = await multipartFormReader(request)
  
  pdfBytesArray = data["pdfTemplate"]
  fileName = data["templateInfo"]["id"]
  
  file = open("temp.pdf", "wb")
  file.write(pdfBytesArray)
  file.close()
  
  pdfDoc = fitz.open("temp.pdf")
  pdfPage = pdfDoc.load_page(0)
  image = pdfPage.get_pixmap()
  image.save(f"public/images/{fileName}.png")
  
  return web.json_response({
    "fileName": fileName,
    "attachment_url": f"http://localhost:{port}/public/images/{fileName}.png"
  })


def savePdfTemplateFile(pdfTemplate, fileName):
  if not os.path.exists("public/templates"):
    os.makedirs("public/templates")
  
  file = open(f"public/templates/{fileName}", "wb")
  file.write(pdfTemplate)
  file.close()


# Read and decode parts of the multipart form
async def multipartFormReader(request):
  reader = aiohttp.MultipartReader.from_response(request)
  requestData = {}
  
  while True:
    # Get next form part
    part = await reader.next()
    
    if part is None:
      break
    
    elif part.headers['Content-Type'] == "application/json":
      byteArrayResult = await part.read(decode=True)
      
      jsonValue = byteArrayResult.decode('utf8').replace("'", '"')
      jsonData = json.loads(jsonValue)
      
      formPartName = part.headers["Content-Disposition"].split(" ")[2]
      
      if formPartName == 'filename="template"':
        requestData["template"] = jsonData
      elif formPartName == 'filename="pdfDimensions"':
        requestData["pdfSize"] = jsonData
      elif formPartName == 'filename="templateInfo"':
        requestData["templateInfo"] = jsonData

    # Get the PDF template
    elif part.headers['Content-Type'] == "application/pdf":
      requestData["pdfTemplate"] = await part.read(decode=True)

  return requestData

###############################################################################

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
  web.run_app(app, port=port)