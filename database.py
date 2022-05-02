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

  name = Required(str)
  tags = Required(StrArray)
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
    tags = template["tags"],

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
def updateTemplate(templateId, updatedTemplate):
  template = Template.get(id=templateId)
  
  template.pdf_dimensions = updatedTemplate["pdfDimensions"]
  template.name = updatedTemplate["name"]
  template.tags = updatedTemplate["tags"]
  template.selection_list = updatedTemplate["selectionList"]
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
  