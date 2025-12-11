from fastapi import FastAPI, Depends, HTTPException, Header, Request, Form, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from .database import engine, init_db, get_session
from .models import User, Command, Rule, AuditLog
from .crud import get_user_by_api_key, create_rule, match_command_against_rules
from .utils import generate_api_key, log_action
from datetime import datetime
import re

# ===================================================================
# QUICK USER REGISTRATION – PUT THIS AT THE VERY BOTTOM OF THE FILE
# ===================================================================
from pydantic import BaseModel

 
app = FastAPI(title="Command Gateway")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

class RegisterRequest(BaseModel):
    username: str
    credits: int = 100

@app.post("/api/register")
def register_user(payload: RegisterRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.username == payload.username)).first()
    if existing:
        return {"error": "Username already taken"}

    api_key = generate_api_key()
    new_user = User(
        username=payload.username,
        api_key=api_key,
        role="member",
        credits=payload.credits
    )
    session.add(new_user)
    session.commit()

    return {
        "username": payload.username,
        "api_key": api_key,
        "credits": payload.credits,
        "message": "SUCCESS! Copy this API key now – you won't see it again!"
    }

@app.on_event("startup")
def on_startup():
    init_db()
    with Session(engine) as session:
        # Seed admin
        if not session.exec(select(User).where(User.username == "admin")).first():
            admin_key = generate_api_key()
            admin = User(username="admin", api_key=admin_key, role="admin", credits=999999)
            session.add(admin)
            session.commit()
            print(f"\nADMIN API KEY: {admin_key}\n")
        default_rules = [
            (r":\(\)\{\s*:\|\:&\s*\};:", "AUTO_REJECT", "Fork bomb"),
            (r"rm\s+-rf\s+/", "AUTO_REJECT", "Dangerous rm"),
            (r"mkfs\..*", "AUTO_REJECT", "Disk format"),
            (r">/dev/sd[a-z]", "AUTO_REJECT", "Write to raw disk"),
            (r"git\s+(status|log|diff|pull|fetch)", "AUTO_ACCEPT", "Safe git"),
            (r"^(ls|pwd|whoami|cat|echo|date|id|clear|exit)(\s|$)", "AUTO_ACCEPT", "Basic commands"),
        ]
        
        
        existing = {r.pattern for r in session.exec(select(Rule)).all()}
        for pat, act, desc in default_rules:
            if pat not in existing:
                create_rule(session, pat, act, desc)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/login")
async def login(request: Request, api_key: str = Form(...)):
    with Session(engine) as session:
        user = get_user_by_api_key(session, api_key)
        if not user:
            raise HTTPException(401, "Invalid API key")
        ctx = {"request": request, "user": user, "api_key": api_key}
        if user.role == "admin":
            return templates.TemplateResponse("admin.html", ctx)
        return templates.TemplateResponse("dashboard.html", ctx)

# === API ===

def get_current_user(api_key: str = Header(None, alias="api_key"), session: Session = Depends(get_session)):
    if not api_key:
        raise HTTPException(401, "Missing API key")
    user = get_user_by_api_key(session, api_key)
    if not user:
        raise HTTPException(401, "Invalid API key")
    return user

 

@app.post("/api/commands")
def submit_command(
    command_text: str = Form(...),
    user=Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if user.credits <= 0:
        log_action(session, user.id, "command_rejected", "Out of credits")
        raise HTTPException(402, "Not enough credits")

    action = match_command_against_rules(session, command_text)

    is_executed = action == "AUTO_ACCEPT"
    result_text = f"[MOCK] Executed: {command_text}" if is_executed else "Command blocked by security rule"

    command = Command(
        user_id=user.id,
        command_text=command_text,
        status="executed" if is_executed else "rejected",
        result=result_text if is_executed else None,
        credits_deducted=1 if is_executed else 0
    )
    session.add(command)

    if is_executed:
        user.credits -= 1
        log_action(session, user.id, "command_executed", command_text)
    else:
        log_action(session, user.id, "command_rejected", f"Blocked: {command_text}")

    session.commit()
    session.refresh(user)

    return {
        "command_text": command_text,
        "status": "executed" if is_executed else "rejected",
        "result": result_text,
        "new_balance": user.credits
    }
@app.get("/api/me")
def me(user=Depends(get_current_user)):
    return {"username": user.username, "role": user.role, "credits": user.credits}

@app.get("/api/commands")
def my_commands(user=Depends(get_current_user), session: Session = Depends(get_session)):
    cmds = session.exec(
        select(Command).where(Command.user_id == user.id).order_by(Command.created_at.desc())
    ).all()
    return cmds

@app.get("/api/rules")
def list_rules(user=Depends(get_current_user), session: Session = Depends(get_session)):
    if user.role != "admin":
        raise HTTPException(403)
    return session.exec(select(Rule)).all()

@app.post("/api/rules")
def add_rule(
    pattern: str = Form(...),
    action: str = Form(...),
    description: str = Form(""),
    user=Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if user.role != "admin":
        raise HTTPException(403)
    rule = create_rule(session, pattern, action, description)
    log_action(session, user.id, "rule_created", f"{pattern} → {action}")
    return rule

@app.get("/api/audit")
def audit_logs(user=Depends(get_current_user), session: Session = Depends(get_session)):
    if user.role != "admin":
        raise HTTPException(403)
    logs = session.exec(select(AuditLog).order_by(AuditLog.timestamp.desc())).all()
    return logs

@app.get("/api/me")
def me(user=Depends(get_current_user)):
    return {"username": user.username, "role": user.role, "credits": user.credits}

 