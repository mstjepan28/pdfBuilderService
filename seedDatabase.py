import database
import uuid
import random
import time
import json

NEW_RECORDS = 15

def actionWillExecute(chance):
  return random.random() < chance

def randomString(stringLength=10):
  letters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
  return ''.join(random.choice(letters) for i in range(stringLength))

def randomTags(numberOfTags):
  tags = []
  for i in range(numberOfTags):
    tags.append(randomString())
  return tags

def randomListFromList(originalList, maxLength, minLength=0):
  selectedList = []
  selectionList = originalList.copy()
  rand = random.randint(minLength, maxLength)
  
  for i in range(rand):
    randIndex = random.randint(0, len(selectionList) - 1)

    selected = selectionList.pop(randIndex)
    selectedList.append(selected)
  
  return selectedList

def getSelectionContent():
  isStatic = actionWillExecute(0.5)
  variables = ["student", "oib", "email", "poduzece", "mentor", "razdoblje_od", "razboblje_do", "broj_sati", "opis_zadatka", "image"]
  
  return (
    random.choice(variables) if isStatic else None, 
    isStatic, 
    randomString(15) if isStatic else None
  )

def getPositionData():
  randX = random.randint(0, 75)
  randY = random.randint(0, 75)
  
  return {
    "x": randX / 100,
    "y": randY / 100,
    "width": random.randint(5, 100 - randX) / 100,
    "height": random.randint(5, 100 - randY) / 100
  }

def validateVariableAndType(variable, type):
  variables = ["student", "oib", "email", "poduzece", "mentor", "razdoblje_od", "razboblje_do", "broj_sati", "opis_zadatka"]

  if type == "image":
    variable = "image"
  elif variable == "image":
    variable = random.choice(variables)
  
  return (variable, type)

def createSelectionList(maxLength):
  selectionList = []
  rand = random.randint(1, maxLength)
  
  for i in range(rand):
    variable, isStatic, staticContent = getSelectionContent()
    type = random.choice(["singleLineText", "paragraph", "image"])
    
    variable, type = validateVariableAndType(variable, type)
  
    selection = {
      "type": type,
      "variable": variable,
      "isStatic": isStatic,
      "internalComponent": type == "image" and isStatic,
      "positionData": getPositionData()
    }
    selectionList.append(selection)
    
  return selectionList

def randomVariableList(maxLength):
  variableList = []
  rand = random.randint(1, maxLength)
  
  for i in range(rand):
    variableList.append({
      "name": randomString(15),
      "type": random.choice(["singleLineText", "paragraph", "image"])
    })
    
  return variableList

# --- # --- # --- # --- # --- # --- # --- #

def seedDatabase():
  database.setupDatabase()

  templateList = []
  tagsList = randomTags(10)

  for i in range(NEW_RECORDS):
    template = {
      "id": str(uuid.uuid4()),
      "baseTemplateId": str(uuid.uuid4()) if actionWillExecute(0.80) else None,
      "pdfDimensions": {
        "width": 596, 
        "height": 842
      },
      
      "createdBy": randomString(20),
      "createdAt": str(time.time() * 1000),
      "updatedAt": str(time.time() * 1000),
    
      "name": randomString(15),
      "tags": randomListFromList(tagsList, 5),
      "variableList": randomVariableList(5),
      
      "selectionList": createSelectionList(7),
    }
    
    database.addTemplate(template)

if __name__ == "__main__":
  choice = input(f"Seeding the database will add another {NEW_RECORDS} templates to the database.\nAre you sure you want to continue? (y/n) ")
  
  if(choice == "y"):
    print("Seeding database...")
    seedDatabase()
    print("Seeding database finished")
  else:
    print("Seeding aborted")