from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from . import crud, models, schemas, auth, ai_agent
from .database import SessionLocal, engine, get_db
# NEW: Import the simulated employee data
from .employee_data import EMPLOYEE_DATA

schemas.Base.metadata.create_all(bind=engine)
app = FastAPI(title="CogniDesk API")

# On Startup: Create default users
@app.on_event("startup")
def create_initial_users():
    db = SessionLocal()
    if not crud.get_user_by_username(db, "admin"):
        admin_user = models.UserCreate(username="admin", password="adminpassword", role="admin")
        crud.create_user(db, admin_user)
        print("Admin user created.")
    if not crud.get_user_by_username(db, "employee"):
        employee_user = models.UserCreate(username="employee", password="emppassword", role="employee")
        crud.create_user(db, employee_user)
        print("Employee user created.")
    db.close()

# --- Authentication Endpoint ---
@app.post("/token", response_model=models.Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- NEW: Employee Data Endpoints ---
@app.get("/employees")
def get_all_employees():
    """Returns the full list of simulated employee data."""
    return EMPLOYEE_DATA

@app.get("/employees/{username}")
def get_employee_by_username(username: str):
    """Returns profile data for a specific employee."""
    for employee in EMPLOYEE_DATA:
        if employee["username"] == username:
            return employee
    raise HTTPException(status_code=404, detail="Employee not found")

# --- Ticket Endpoints (No changes needed here) ---
@app.post("/tickets/", response_model=models.Ticket, status_code=status.HTTP_201_CREATED)
def create_new_ticket(ticket: models.TicketCreate, db: Session = Depends(get_db)):
    # This simplified version assumes the logged-in user is 'employee'.
    # A real app would get the user from the JWT token.
    user = crud.get_user_by_username(db, "employee")
    if not user:
        raise HTTPException(status_code=404, detail="Default user not found")
    
    db_ticket = crud.create_ticket(db=db, ticket=ticket, user_id=user.id)
    ai_result = ai_agent.process_query_with_ai(ticket.query)
    updated_ticket = crud.update_ticket(
        db=db, 
        ticket_id=db_ticket.id, 
        response=ai_result["response"], 
        status=ai_result["status"]
    )
    return updated_ticket

@app.get("/tickets/", response_model=List[models.Ticket])
def read_all_tickets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_tickets(db, skip=skip, limit=limit)

@app.get("/tickets/{ticket_id}", response_model=models.Ticket)
def read_single_ticket(ticket_id: int, db: Session = Depends(get_db)):
    db_ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return db_ticket