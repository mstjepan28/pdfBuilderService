from pony.orm import *
from datetime import datetime
import env
import os

DB = Database()

class Template(DB.Entity):
  id = PrimaryKey(str, auto=False)
  base_template_id = Optional(str, nullable=True)
  pdf_dimensions = Required(Json)

  created_by = Required(str)
  created_at = Required(str)
  updated_at = Required(str)

  name = Required(str, unique=True)
  variable_list = Required(Json)
  
  selection_list = Required(Json)

@db_session
def addTemplate(template):
  Template(
    id = template["id"],
    base_template_id = template["baseTemplateId"],
    pdf_dimensions = template["pdfDimensions"],

    created_by = template["createdBy"],
    created_at = template["createdAt"],
    updated_at = template["updatedAt"],

    name = template["name"],
    variable_list = template["variableList"],

    selection_list = template["selectionList"]
  )

@db_session
def getAllTemplates():
  templates = select(t for t in Template)
  return [t.to_dict() for t in templates]


@db_session
def getTemplateById(templateId):
  template = Template.get(id=templateId)
  return template.to_dict() if template else None


@db_session
def getTemplateByName(templateName):
  template = Template.get(name=templateName)
  return template.to_dict() if template else None


@db_session
def templateWithNameExists(name, getTemplateId=False):
  template = Template.get(name=name)
  
  if not template:
    return False
  
  template = template.to_dict()
  return template["id"] if getTemplateId else True

@db_session
def updateTemplate(templateId, updatedTemplate):
  template = Template.get(id=templateId)
  
  template.base_template_id = updatedTemplate["baseTemplateId"]
  template.pdf_dimensions = updatedTemplate["pdfDimensions"]
  template.name = updatedTemplate["name"]
  template.selection_list = updatedTemplate["selectionList"]
  template.variable_list = updatedTemplate["variableList"]
  template.updated_at = str(datetime.now())


@db_session
def deleteTemplate(templateId):
  template = Template.get(id=templateId)

  if template:
    template.delete()
    return True
  else:
    return False

def setupDatabase():
  if not os.path.isdir("database"):
    os.mkdir("database")
  if env.DB["provider"] == "postgres":
    DB.bind(**env.DB)
  else:
    DB.bind(provider="sqlite", filename="database/database.sqlite", create_db=True)
  DB.generate_mapping(create_tables=True)
  