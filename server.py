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
from zipfile import ZipFile

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
  
  savePdfTemplateFile(data["pdfTemplate"], str(template['id']))
  
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
  
  deleteTemplateDirectory(templateId)
  
  return web.json_response({"success": success})

###############################################################################

@routes.get("/templates/{id}/files")
async def getGeneratedFileNames(request):
  templateId = request.match_info.get("id")
  
  fileList = getGeneratedFiles(templateId)
  return web.json_response(fileList)


@routes.post("/templates/{id}/files/generate")
async def generateFiles(request):
  templateId = request.match_info.get("id")
  
  template = database.getTemplateById(templateId)
  mockData = getTestingData()
  
  fileGenerator(template, mockData)
  fileList = getGeneratedFiles(templateId)
  
  return web.json_response(fileList)
  

@routes.post("/templates/{id}/files")
async def getGeneratedFiles(request):
  templateId = request.match_info.get("id")
  data = await request.json()
  fileList = data["fileList"]
  
  responseFile = None
  
  if len(fileList) > 1:
    responseFile = zipTemplateFiles(templateId, fileList)
  else:
    responseFile = web.FileResponse(f"public/{templateId}/generated/{fileList[0]}")
  
  return responseFile


@routes.post("/templates/{id}/files/remove")
async def deleteGeneratedFiles(request):
  templateId = request.match_info.get("id")
  data = await request.json()
  fileList = data["fileList"]
  
  deleteGeneratedFiles(templateId, fileList)
  
  return web.json_response({"success": True})

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
  
  file = open("temp.pdf", "wb")
  file.write(pdfBytesArray)
  file.close()
  
  pdfDoc = fitz.open("temp.pdf")
  pdfPage = pdfDoc.load_page(0)
  image = pdfPage.get_pixmap()
  
  templateDir = templateDirectoryExist(data["templateInfo"]["id"])
  filePath = f"{templateDir}/background.png"
  image.save(filePath)
  
  return web.json_response({
    "attachment_url": f"http://localhost:{port}/{filePath}"
  })

###############################################################################

def deleteGeneratedFiles(templateId, fileList):
  filePath = f"./public/{templateId}/generated"
  
  curWrkDir = os.getcwd()
  os.chdir(filePath)
  
  for file in os.listdir():
    if file in fileList:
      os.remove(file)

  os.chdir(curWrkDir)


def zipTemplateFiles(templateId, fileList):
  filePath = f"./public/{templateId}/generated"
  zipFileName = f"../{templateId}.zip"
  zipFilePath = f"./public/{templateId}/{templateId}.zip"
  
  curWrkDir = os.getcwd()
  os.chdir(filePath)
  
  with ZipFile(zipFileName, 'w') as newZipFile:
    for file in os.listdir():
      if file in fileList:
        newZipFile.write(file)

  os.chdir(curWrkDir)

  return web.FileResponse(zipFilePath)


def getGeneratedFiles(templateId):
  filePath = f"public/{templateId}/generated"
  if not os.path.exists(filePath):
    os.makedirs(filePath)
    return []
  
  return os.listdir(filePath)


def savePdfTemplateFile(pdfTemplate, fileName):
  filePath = templateDirectoryExist(fileName)
  
  file = open(f"{filePath}/{fileName}.pdf", "wb")
  file.write(pdfTemplate)
  file.close()


def templateDirectoryExist(templateId):
  filePath = f"public/{templateId}"
  if not os.path.exists(filePath):
    os.makedirs(filePath)
  
  return filePath


def deleteTemplateDirectory(templateId):
  filePath = f"public/{templateId}"
  if not os.path.exists(filePath):
    return

  for file in os.listdir(filePath):
    os.remove(f"{filePath}/{file}")
  
  os.rmdir(filePath)


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