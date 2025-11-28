from sqlalchemy.orm import Session
from . import models, schemas, auth

def get_user_by_username(db: Session, username: str):
    return db.query(schemas.User).filter(schemas.User.username == username).first()

def create_user(db: Session, user: models.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = schemas.User(username=user.username, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_ticket(db: Session, ticket: models.TicketCreate, user_id: int):
    db_ticket = schemas.Ticket(**ticket.model_dump(), owner_id=user_id)
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def get_tickets(db: Session, skip: int = 0, limit: int = 100):
    return db.query(schemas.Ticket).offset(skip).limit(limit).all()

def get_ticket(db: Session, ticket_id: int):
    return db.query(schemas.Ticket).filter(schemas.Ticket.id == ticket_id).first()

def update_ticket(db: Session, ticket_id: int, response: str, status: str):
    db_ticket = get_ticket(db, ticket_id)
    if db_ticket:
        db_ticket.response = response
        db_ticket.status = status
        db.commit()
        db.refresh(db_ticket)
    return db_ticket