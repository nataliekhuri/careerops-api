
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="CareerOps API",
    description="An API to manage job applications",
    version="1.0.0"
)

# Temporary storage
applications = []
next_id = 1


class JobApplication(BaseModel):
    company: str
    position: str
    status: str = "Applied"
    location: str
    notes: str = ""


@app.get("/")
def home():
    return {
        "message": "Welcome to CareerOps API!",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Create a job application
@app.post("/applications")
def create_application(application: JobApplication):
    global next_id

    new_application = {
        "id": next_id,
        **application.model_dump()
    }

    applications.append(new_application)
    next_id += 1

    return {
        "message": "Application created successfully",
        "application": new_application
    }


# Get all applications
@app.get("/applications")
def get_applications():
    return applications


# Get one application by ID
@app.get("/applications/{application_id}")
def get_application(application_id: int):
    for application in applications:
        if application["id"] == application_id:
            return application

    raise HTTPException(
        status_code=404,
        detail="Application not found"
    )


# Update an application
@app.put("/applications/{application_id}")
def update_application(
    application_id: int,
    updated_application: JobApplication
):
    for index, application in enumerate(applications):
        if application["id"] == application_id:
            applications[index] = {
                "id": application_id,
                **updated_application.model_dump()
            }
            return applications[index]

    raise HTTPException(
        status_code=404,
        detail="Application not found"
    )


# Delete an application
@app.delete("/applications/{application_id}")
def delete_application(application_id: int):
    for index, application in enumerate(applications):
        if application["id"] == application_id:
            deleted_application = applications.pop(index)
            return {
                "message": "Application deleted successfully",
                "application": deleted_application
            }

    raise HTTPException(
        status_code=404,
        detail="Application not found"
    )
