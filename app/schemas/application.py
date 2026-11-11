from pydantic import BaseModel, ConfigDict


class JobApplication(BaseModel):
    """Request body for creating or replacing an application."""

    company: str
    position: str
    status: str = "Applied"
    location: str
    notes: str = ""


class ApplicationRead(BaseModel):
    """An application as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    position: str
    status: str
    location: str
    notes: str


class ApplicationMessage(BaseModel):
    """Response for create and delete: a message plus the application."""

    message: str
    application: ApplicationRead
