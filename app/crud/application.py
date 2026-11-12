from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.schemas.application import JobApplication


def create_application(db: Session, data: JobApplication) -> Application:
    application = Application(**data.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def list_applications(db: Session) -> list[Application]:
    return list(db.scalars(select(Application).order_by(Application.id)))


def get_application(db: Session, application_id: int) -> Application | None:
    return db.get(Application, application_id)


def update_application(db: Session, application: Application, data: JobApplication) -> Application:
    for field, value in data.model_dump().items():
        setattr(application, field, value)
    db.commit()
    db.refresh(application)
    return application


def delete_application(db: Session, application: Application) -> None:
    db.delete(application)
    db.commit()
