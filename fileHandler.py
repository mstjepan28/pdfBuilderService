from zipfile import ZipFile # files
import shutil # files
import os 

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
  
  curWrkDir = os.getcwd()
  os.chdir(filePath)
  
  files = os.listdir()
  files.sort(key=os.path.getctime)
  
  os.chdir(curWrkDir)
  
  return files[:10]


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

  shutil.rmtree(filePath)  

