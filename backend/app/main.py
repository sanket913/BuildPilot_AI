from datetime import date, timedelta
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from pypdf import PdfReader
from docx import Document as DocxDocument
from io import BytesIO
import hmac
import json
import logging
from datetime import datetime
from . import db, schemas, ai
from .config import settings
from .integrations.nonilion import adapter as nonilion

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("buildpilot.api")
is_production = settings.app_env.lower() == "production"
app = FastAPI(
    title="BuildPilot AI API",
    version="1.0.0",
    description="Hackathon project execution workspace",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)
origins = [origin.strip().rstrip("/") for origin in settings.frontend_origin.split(",") if origin.strip()]
if not is_production:
    origins.extend(["http://localhost:5173", "http://127.0.0.1:5173"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(set(origins)),
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,
)

@app.middleware("http")
async def access_control(request: Request, call_next):
    if request.method != "OPTIONS" and settings.app_access_token and request.url.path.startswith("/api/") and request.url.path != "/api/health":
        supplied = request.headers.get("authorization", "")
        expected = f"Bearer {settings.app_access_token}"
        if not hmac.compare_digest(supplied, expected):
            response = JSONResponse(status_code=401, content={"detail": "Workspace access code required"})
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Cache-Control"] = "no-store"
            return response
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-Frame-Options", "DENY")
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response

db.init_db()

def get_session():
    session = db.SessionLocal()
    try: yield session
    finally: session.close()

def get_project(session: Session, project_id: int):
    project = session.get(db.Project, project_id)
    if not project: raise HTTPException(404, "Project not found")
    return project

def record(session: Session, project_id: int, message: str):
    session.add(db.Activity(project_id=project_id, message=message))

def serialize(obj):
    result = {column.name: getattr(obj, column.name) for column in obj.__table__.columns}
    return {key: value.isoformat() if hasattr(value, "isoformat") else value for key, value in result.items()}

@app.get("/api/health")
def health():
    try:
        with db.engine.connect() as connection:
            connection.execute(sql_text("SELECT 1"))
    except Exception:
        logger.exception("Health check failed: database is unavailable")
        raise HTTPException(503, "Database is unavailable")
    return {
        "status": "ok",
        "ai_mode": "configured" if settings.ai_api_key else "demo",
        "access_controlled": bool(settings.app_access_token),
    }

@app.get("/api/integrations/nonilion")
async def nonilion_status(): return await nonilion.connection_status()

@app.get("/api/projects")
def projects(session: Session = Depends(get_session)): return [serialize(p) for p in session.query(db.Project).order_by(db.Project.id).all()]

@app.get("/api/demo")
def demo_status(session: Session = Depends(get_session)):
    project = session.query(db.Project).filter_by(is_demo=True).first()
    return {"available": project is not None, "project_id": project.id if project else None}

@app.post("/api/demo")
def seed_demo(session: Session = Depends(get_session)):
    project = session.query(db.Project).filter_by(is_demo=True).first()
    if project: return {"project_id": project.id, "already_seeded": True}
    statement = "Campus teams discard food while nearby community fridges run low. Build a reliable way to match surplus meals with local need, while respecting food safety and volunteer capacity."
    analysis = ai.analyze_fallback(statement)
    analysis.update({"title": "Campus Food Loop", "objective": "Coordinate safe, timely food donations from campus dining to nearby community fridges.", "domain": "Food access and sustainability", "target_users": ["Campus dining staff", "Community fridge volunteers"], "functional_requirements": ["List surplus meals", "Match donations with pickup capacity", "Track pickup status"], "constraints": ["Food safety and expiry windows", "Volunteer availability"], "recommendation": "Prototype the donation-to-pickup workflow with clear safety and expiry fields."})
    solution = {"name": "Campus Food Loop", "summary": "A lightweight coordination board for safe campus food redistribution.", "approach": "Dining staff post time-bound surplus lots; volunteers claim pickup slots; fridge coordinators confirm receipt.", "features": ["Surplus listings", "Pickup claims", "Expiry and safety notes", "Fridge capacity view"], "architecture": "React client, FastAPI service, PostgreSQL database", "stack": ["React", "TypeScript", "FastAPI", "PostgreSQL"], "ai_components": ["Optional demand summary from listing history"], "data_design": "Users, donation lots, pickup claims, fridge locations", "api_design": "REST endpoints for listings, claims, and status changes", "phases": ["Discovery", "Core workflow", "Safety checks", "Demo and submission"], "impact": "Measure successful pickups and food diverted from waste.", "limitations": ["Pilot requires partner validation and food safety review."]}
    today = date.today()
    project = db.Project(name="Campus Food Loop", description="A coordination tool that routes campus surplus meals to community fridges.", hackathon_name="Sustainable Campus Sprint", start_date=today - timedelta(days=3), deadline=today + timedelta(days=5), status="In Progress", is_demo=True, problem_statement=statement, analysis=json.dumps(analysis), solution=json.dumps(solution))
    session.add(project); session.flush()
    team = [("Aarav Shah", "Backend + AI", "Python, FastAPI, SQL", "Advanced", "API design, data model"), ("Mira Patel", "AI/ML Engineer", "Python, Machine Learning, NLP", "Intermediate", "Demand insights, analysis"), ("Dev Nair", "Web Developer", "React, TypeScript, CSS", "Intermediate", "Frontend, accessibility"), ("Isha Rao", "Product + Full-stack", "Web development, UX research, Python", "Intermediate", "User research, integration")]
    for name, role, skills, experience, responsibilities in team: session.add(db.Member(project_id=project.id, name=name, role=role, skills=skills, experience_level=experience, responsibilities=responsibilities, availability="8 hours / week"))
    task_data = [
        ("Map donation and pickup journey", "Document donor, volunteer, and fridge handoffs plus food safety constraints.", "Completed", "High", "Isha Rao", "Research and planning", "3 hours", "The team agrees on one safe donation-to-pickup journey.", today - timedelta(days=2), ""),
        ("Set up project API and data model", "Define donation, pickup, and fridge records with validation.", "Completed", "High", "Aarav Shah", "Architecture and setup", "4 hours", "The API starts locally and persists a validated sample record.", today - timedelta(days=1), "Map donation and pickup journey"),
        ("Create donation listing API", "Validate listing fields, expiry windows, and pickup status changes.", "In Progress", "Critical", "Aarav Shah", "Core development", "6 hours", "A donation can be created, claimed, and marked picked up.", today + timedelta(days=1), "Set up project API and data model"),
        ("Build surplus listing board", "Create a responsive board with expiry and pickup filters.", "Review", "High", "Dev Nair", "Core development", "5 hours", "A volunteer can find an available lot on a mobile screen.", today + timedelta(days=1), "Create donation listing API"),
        ("Summarize demand patterns", "Prototype a transparent summary from the supplied sample listings.", "To Do", "Medium", "Mira Patel", "AI/ML implementation", "4 hours", "The summary states its sample size and does not invent demand.", today + timedelta(days=2), "Create donation listing API"),
        ("Connect listing and pickup workflow", "Wire the web board to listing, claim, and confirmation API operations.", "To Do", "High", "Dev Nair", "Frontend and backend integration", "5 hours", "A listing stays in sync after a volunteer claims it.", today + timedelta(days=2), "Build surplus listing board; Create donation listing API"),
        ("Confirm food safety handoff checklist", "Review temperature, expiry, allergen, and pickup confirmation fields with a partner.", "To Do", "Critical", "", "Testing and debugging", "2 hours", "A partner reviews the checklist and the demo blocks unsafe handoffs.", today - timedelta(days=1), ""),
        ("Deploy the preview environment", "Configure the hosted frontend, API, and persistent database.", "To Do", "Medium", "Aarav Shah", "Deployment", "3 hours", "The health check passes and a saved project survives a restart.", today + timedelta(days=3), ""),
        ("Rehearse and finalize submission", "Run the demo from a fresh session and prepare the final presentation.", "To Do", "Medium", "Isha Rao", "Presentation and submission", "2 hours", "A teammate can reproduce the demo from the README.", today + timedelta(days=4), "Deploy the preview environment"),
    ]
    for title, description, status, priority, assignee, phase, effort, criteria, due_date, dependencies in task_data:
        session.add(db.Task(project_id=project.id, title=title, description=description, status=status, priority=priority, assignee=assignee, phase=phase, estimated_effort=effort, acceptance_criteria=criteria, due_date=due_date, dependencies=dependencies))
    checklist = ["Problem analyzed", "Solution finalized", "Architecture completed", "Core development completed", "Frontend integrated", "Backend integrated", "AI features tested", "Testing completed", "GitHub repository ready", "Deployment verified", "README completed", "Presentation ready", "Demo verified"]
    for index, title in enumerate(checklist): session.add(db.Check(project_id=project.id, title=title, done=index in {0, 1, 2, 10}))
    readme = f"# Campus Food Loop\n\n{project.description}\n\n## Problem\n\n{statement}\n\n## Solution\n\n{solution['summary']}\n\n## Stack\n\nReact, TypeScript, FastAPI, PostgreSQL.\n\n## Setup\n\nRun the frontend and API in separate terminals.\n\n## Testing\n\nVerify donation listing, pickup claim, confirmation, safety notes, and mobile layout.\n\n## Future scope\n\nPilot with campus dining and community fridge partners.\n"
    session.add(db.Document(project_id=project.id, title="README.md", content=readme))
    for message in ["Sample project seeded", "Problem brief analyzed and solution saved", "Four sample team profiles added", "Eight roadmap phases populated with mixed task statuses", "Submission checklist and README prepared"]:
        record(session, project.id, message)
    session.commit(); return {"project_id": project.id, "already_seeded": False}

@app.delete("/api/demo")
def reset_demo(session: Session = Depends(get_session)):
    for project in session.query(db.Project).filter_by(is_demo=True).all(): session.delete(project)
    session.commit(); return {"ok": True}

@app.post("/api/projects")
def create_project(body: schemas.ProjectIn, session: Session = Depends(get_session)):
    project = db.Project(**body.model_dump())
    session.add(project); session.flush()
    for title in ["Problem statement analyzed", "Solution finalized", "Architecture documented", "Core functionality implemented", "Frontend completed", "Backend completed", "AI integration tested", "Application tested", "GitHub repository prepared", "Deployment verified", "README completed", "Presentation prepared", "Demo tested"]:
        session.add(db.Check(project_id=project.id, title=title))
    session.flush(); record(session, project.id, "Project created"); session.commit(); session.refresh(project); return serialize(project)

@app.get("/api/projects/{pid}")
def project_detail(pid: int, session: Session = Depends(get_session)):
    p = get_project(session, pid)
    return {**serialize(p), "analysis": json.loads(p.analysis) if p.analysis else None, "solution": json.loads(p.solution) if p.solution else None, "members": [serialize(x) for x in p.members], "tasks": [serialize(x) for x in p.tasks], "checks": [serialize(x) for x in p.checks], "documents": [serialize(x) for x in p.documents], "activities": [serialize(x) for x in sorted(p.activities, key=lambda a: a.created_at, reverse=True)[:10]]}

@app.patch("/api/projects/{pid}")
def update_project(pid: int, body: schemas.ProjectIn, session: Session = Depends(get_session)):
    p = get_project(session, pid)
    for key, value in body.model_dump().items(): setattr(p, key, value)
    record(session, pid, "Project details updated"); session.commit(); return serialize(p)

@app.put("/api/projects/{pid}/solution")
def save_solution(pid: int, body: schemas.SolutionSave, session: Session = Depends(get_session)):
    p = get_project(session, pid); p.solution = body.solution.model_dump_json(); record(session, pid, "Solution proposal saved"); session.commit(); return body.solution.model_dump()

@app.post("/api/projects/{pid}/archive")
def archive_project(pid: int, session: Session = Depends(get_session)):
    p = get_project(session, pid); p.archived = not p.archived; record(session, pid, "Project archived" if p.archived else "Project restored"); session.commit(); return serialize(p)

@app.get("/api/projects/{pid}/activity")
def project_activity(pid: int, session: Session = Depends(get_session)):
    p = get_project(session, pid)
    return [serialize(a) for a in sorted(p.activities, key=lambda a: a.created_at, reverse=True)[:30]]

@app.delete("/api/projects/{pid}")
def delete_project(pid: int, session: Session = Depends(get_session)):
    p = get_project(session, pid); session.delete(p); session.commit(); return {"ok": True}

@app.post("/api/projects/{pid}/members")
def add_member(pid: int, body: schemas.MemberIn, session: Session = Depends(get_session)):
    get_project(session, pid); m = db.Member(project_id=pid, **body.model_dump()); session.add(m); record(session, pid, f"{m.name} joined the team"); session.commit(); session.refresh(m); return serialize(m)

@app.delete("/api/members/{mid}")
def delete_member(mid: int, session: Session = Depends(get_session)):
    m = session.get(db.Member, mid)
    if not m: raise HTTPException(404, "Team member not found")
    project_id = m.project_id
    for task in session.query(db.Task).filter_by(project_id=project_id, assignee=m.name).all(): task.assignee = ""
    record(session, project_id, f"{m.name} was removed from the team; their tasks are now unassigned")
    session.delete(m); session.commit(); return {"ok": True}

@app.patch("/api/members/{mid}")
def update_member(mid: int, body: schemas.MemberIn, session: Session = Depends(get_session)):
    member = session.get(db.Member, mid)
    if not member: raise HTTPException(404, "Team member not found")
    for key, value in body.model_dump().items(): setattr(member, key, value)
    record(session, member.project_id, f"Team profile updated: {member.name}"); session.commit(); return serialize(member)

@app.post("/api/projects/{pid}/tasks")
def add_task(pid: int, body: schemas.TaskIn, session: Session = Depends(get_session)):
    project = get_project(session, pid)
    if body.assignee and body.assignee not in {m.name for m in project.members}: raise HTTPException(422, "Assignee must be a member of this project")
    task = db.Task(project_id=pid, **body.model_dump()); session.add(task); record(session, pid, f"Task created: {task.title}"); session.commit(); session.refresh(task); return serialize(task)

@app.patch("/api/tasks/{tid}")
def update_task(tid: int, body: schemas.TaskIn, session: Session = Depends(get_session)):
    task = session.get(db.Task, tid)
    if not task: raise HTTPException(404, "Task not found")
    project = get_project(session, task.project_id)
    if body.assignee and body.assignee not in {m.name for m in project.members}: raise HTTPException(422, "Assignee must be a member of this project")
    old_status = task.status
    for key, value in body.model_dump().items(): setattr(task, key, value)
    if old_status != task.status: record(session, task.project_id, f"{task.title}: {old_status} → {task.status}")
    else: record(session, task.project_id, f"Task updated: {task.title}")
    session.commit(); return serialize(task)

@app.delete("/api/tasks/{tid}")
def delete_task(tid: int, session: Session = Depends(get_session)):
    task = session.get(db.Task, tid)
    if not task: raise HTTPException(404, "Task not found")
    record(session, task.project_id, f"Task deleted: {task.title}"); session.delete(task); session.commit(); return {"ok": True}

@app.patch("/api/checks/{cid}")
def update_check(cid: int, body: schemas.CheckIn, session: Session = Depends(get_session)):
    check = session.get(db.Check, cid)
    if not check: raise HTTPException(404, "Checklist item not found")
    check.title = body.title; check.done = body.done; record(session, check.project_id, f"Checklist updated: {check.title}"); session.commit(); return serialize(check)

@app.post("/api/projects/{pid}/checks")
def add_check(pid: int, body: schemas.CheckIn, session: Session = Depends(get_session)):
    get_project(session, pid); check = db.Check(project_id=pid, **body.model_dump()); session.add(check); record(session, pid, f"Submission item added: {check.title}"); session.commit(); session.refresh(check); return serialize(check)

@app.delete("/api/checks/{cid}")
def delete_check(cid: int, session: Session = Depends(get_session)):
    check = session.get(db.Check, cid)
    if not check: raise HTTPException(404, "Checklist item not found")
    record(session, check.project_id, f"Submission item removed: {check.title}"); session.delete(check); session.commit(); return {"ok": True}

@app.post("/api/projects/{pid}/documents")
def save_document(pid: int, body: schemas.DocIn, session: Session = Depends(get_session)):
    get_project(session, pid); doc = session.query(db.Document).filter_by(project_id=pid, title=body.title).first()
    if not doc: doc = db.Document(project_id=pid, title=body.title); session.add(doc)
    doc.content = body.content; session.commit(); session.refresh(doc); return serialize(doc)

@app.post("/api/projects/{pid}/documents/generate")
async def generate_documentation(pid: int, session: Session = Depends(get_session)):
    project = get_project(session, pid)
    members = [{"name": m.name, "role": m.role, "skills": m.skills} for m in project.members]
    tasks = [{"title": t.title, "status": t.status, "phase": t.phase} for t in project.tasks]
    fallback_content = "\n".join([
        f"# {project.name}", "", project.description, "",
        "## Hackathon", project.hackathon_name or "Not specified", "",
        "## Problem statement", project.problem_statement or "Add the source problem statement.", "",
        "## Problem analysis", project.analysis or "Analysis has not been saved.", "",
        "## Proposed solution", project.solution or "Solution proposal has not been saved.", "",
        "## Team", *[f"- {m['name']} — {m['role']}; skills: {m['skills'] or 'not listed'}" for m in members], "",
        "## Roadmap snapshot", *[f"- [{t['status']}] {t['title']} ({t['phase']})" for t in tasks], "",
        "## Technology stack", "React, TypeScript, FastAPI, SQLAlchemy; configure the selected database for your deployment.", "",
        "## Setup", "Install backend requirements and frontend npm packages. Start FastAPI and Vite in separate terminals.", "",
        "## API documentation", "See the FastAPI OpenAPI page at /docs while the API is running.", "",
        "## Testing strategy", "Test the principal user journey, validation errors, persistence after restart, and mobile layouts.", "",
        "## Future scope", "Validate assumptions with users and extend only after the hackathon prototype proves useful.", ""])
    fallback = {"content": fallback_content}
    prompt = "Generate a useful README.md in Markdown from this real project data. Preserve unknown fields as unknown; do not invent claims. Include project overview, problem analysis, solution, architecture, stack, install/run, API outline, tests, deployment, and future scope. Return JSON with a single content string.\n\n" + json.dumps({"project": serialize(project), "analysis": project.analysis, "solution": project.solution, "team": members, "tasks": tasks}, default=str)[:18000]
    result = await ai.ask(prompt, fallback, schemas.TextOut)
    doc = session.query(db.Document).filter_by(project_id=pid, title="README.md").first()
    if not doc: doc = db.Document(project_id=pid, title="README.md"); session.add(doc)
    doc.content = result["result"]["content"]; record(session, pid, "Project documentation generated"); session.commit()
    return result

@app.get("/api/projects/{pid}/documentation.md", response_class=PlainTextResponse)
def export_documentation(pid: int, session: Session = Depends(get_session)):
    p = get_project(session, pid)
    doc = session.query(db.Document).filter_by(project_id=pid).first()
    return doc.content if doc else f"# {p.name}\n\n{p.description}\n\n## Setup\n\nAdd installation and run instructions here.\n"

@app.post("/api/analyze")
async def analyze(text: str = Form(default=""), project_id: int | None = Form(default=None), file: UploadFile | None = File(default=None), session: Session = Depends(get_session)):
    if file:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in {".pdf", ".docx", ".txt", ".md", ".markdown"}:
            raise HTTPException(415, "Upload a PDF, DOCX, TXT, or Markdown file")
        data = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
        if len(data) > settings.max_upload_mb * 1024 * 1024: raise HTTPException(413, "File exceeds upload size limit")
        try:
            if suffix == ".pdf": text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages)
            elif suffix == ".docx": text = "\n".join(p.text for p in DocxDocument(BytesIO(data)).paragraphs)
            elif suffix in {".txt", ".md", ".markdown"}: text = data.decode("utf-8")
        except HTTPException: raise
        except UnicodeDecodeError as exc: raise HTTPException(400, "Text files must use UTF-8 encoding") from exc
        except Exception as exc:
            logger.info("Document extraction failed for extension %s (%s)", suffix, type(exc).__name__)
            raise HTTPException(400, "Could not extract text from this document; check that it is a valid, readable file") from exc
    if not text.strip(): raise HTTPException(400, "Provide problem statement text or a supported file")
    if len(text) > 100_000: raise HTTPException(413, "Problem statement text exceeds the 100,000 character limit")
    fallback = ai.analyze_fallback(text)
    result = await ai.ask("Analyze this hackathon problem statement. Return valid data for title, summary, objective, domain, target_users, functional_requirements, non_functional_requirements, constraints, deliverables, evaluation_criteria, risks, missing_information, recommendation, confidence_note. Do not invent facts; distinguish absent information and recommendations.\n\n" + text[:20000], fallback, schemas.AnalysisOut)
    if project_id:
        project = get_project(session, project_id); project.problem_statement = text; project.analysis = json.dumps(result["result"]); record(session, project_id, "Problem statement analyzed"); session.commit()
    result["source_text"] = text
    return result

@app.put("/api/projects/{pid}/analysis")
def save_analysis(pid: int, body: schemas.AnalysisSave, session: Session = Depends(get_session)):
    project = get_project(session, pid); project.problem_statement = body.problem_statement; project.analysis = body.analysis.model_dump_json(); record(session, pid, "Problem analysis saved"); session.commit(); return {"problem_statement": project.problem_statement, "analysis": body.analysis.model_dump()}

@app.post("/api/solution")
async def solution(payload: dict):
    prompt = "Generate a realistic hackathon solution proposal. Return JSON keys name, summary, approach, features, architecture, stack, ai_components, data_design, api_design, phases, impact, limitations. Brief and team context: " + str(payload)[:10000]
    fallback = {"name": "Challenge prototype", "summary": "Build a focused MVP around the core user need.", "approach": "Validate the primary workflow, implement it end to end, then prepare a demo.", "features": ["Core user flow", "Progress tracking", "Submission export"], "architecture": "Web client, API service, relational database", "stack": ["React", "FastAPI", "SQLite"], "ai_components": [], "data_design": "Store projects, members, tasks, and checklist items.", "api_design": "REST endpoints for project and task CRUD.", "phases": ["Scope", "Build", "Validate", "Present"], "impact": "To be evaluated with target users.", "limitations": ["Demo guidance; validate against actual challenge constraints"]}
    result = await ai.ask(prompt, fallback, schemas.SolutionOut)
    if payload.get("project_id"):
        with db.SessionLocal() as session:
            project = get_project(session, payload["project_id"]); project.solution = json.dumps(result["result"]); record(session, project.id, "Solution proposal generated"); session.commit()
    return result

@app.post("/api/roadmap")
async def roadmap(payload: dict):
    fallback = {"tasks": [
        {"title":"Define users and success measures","description":"Confirm primary users, constraints, and a measurable demo outcome.","phase":"Research and planning","priority":"High","acceptance_criteria":"The team agrees on one target workflow and success measure.","estimated_effort":"2 hours"},
        {"title":"Set up architecture and data model","description":"Define API boundaries, project entities, and a runnable development setup.","phase":"Architecture and setup","priority":"High","acceptance_criteria":"The client and API run locally and persist a sample record.","estimated_effort":"3 hours","dependencies":["Define users and success measures"]},
        {"title":"Build the core workflow","description":"Implement the primary end-to-end user flow and validation.","phase":"Core development","priority":"Critical","acceptance_criteria":"A user can complete the primary flow and see its saved result.","estimated_effort":"6 hours","dependencies":["Set up architecture and data model"]},
        {"title":"Implement AI/ML component","description":"Add a scoped model workflow with validated output and an explicit fallback.","phase":"AI/ML implementation","priority":"High","acceptance_criteria":"Valid output is schema-checked and provider failures are visible.","estimated_effort":"4 hours","dependencies":["Build the core workflow"]},
        {"title":"Integrate frontend and backend","description":"Connect screens to API operations and handle loading, empty, and error states.","phase":"Frontend and backend integration","priority":"High","acceptance_criteria":"The main journey persists after refresh and communicates API errors.","estimated_effort":"4 hours","dependencies":["Build the core workflow"]},
        {"title":"Test and debug the demo journey","description":"Exercise the main user journey, edge cases, and mobile layout.","phase":"Testing and debugging","priority":"High","acceptance_criteria":"The team records test results and fixes blocking defects.","estimated_effort":"3 hours","dependencies":["Integrate frontend and backend"]},
        {"title":"Deploy the application","description":"Configure a hosted API, frontend, and persistent database.","phase":"Deployment","priority":"Medium","acceptance_criteria":"Deployed health check passes and data survives a restart.","estimated_effort":"2 hours","dependencies":["Test and debug the demo journey"]},
        {"title":"Prepare presentation and submission","description":"Finalize README, demo script, slides, and submission checklist.","phase":"Presentation and submission","priority":"Medium","acceptance_criteria":"A teammate can reproduce the demo from the README.","estimated_effort":"2 hours","dependencies":["Deploy the application"]}
    ]}
    result = await ai.ask("Create realistic roadmap tasks with title, description, phase, priority, assignee (only provided member names), dependencies, acceptance_criteria, estimated_effort, and due_date. Context: " + str(payload)[:10000], fallback, schemas.RoadmapOut)
    if payload.get("project_id"):
        with db.SessionLocal() as session:
            project = get_project(session, payload["project_id"]); allowed = {member.name for member in project.members}
            for item in result["result"]["tasks"]:
                if item.get("assignee") not in allowed: item["assignee"] = ""
                if item.get("assignee"):
                    assigned = next(member for member in project.members if member.name == item["assignee"])
                    task_words = set((item["title"] + " " + item["description"] + " " + item["phase"]).lower().replace("/", " ").split())
                    skill_words = set((assigned.skills + " " + assigned.role + " " + assigned.responsibilities).lower().replace(",", " ").split())
                    if not task_words & skill_words: item["assignee"] = ""
                if item.get("due_date") and isinstance(item["due_date"], str): item["due_date"] = date.fromisoformat(item["due_date"])
                task_data = {**item, "project_id": project.id, "dependencies": ", ".join(item.get("dependencies", [])) if isinstance(item.get("dependencies"), list) else item.get("dependencies", "")}
                session.add(db.Task(**task_data))
            record(session, project.id, f"Roadmap generated with {len(result['result']['tasks'])} tasks"); session.commit()
    return result

@app.post("/api/projects/{pid}/allocate")
async def allocate_tasks(pid: int, session: Session = Depends(get_session)):
    project = get_project(session, pid); members = project.members; tasks = [task for task in project.tasks if task.status != "Completed"]
    def choose(task):
        tokens = set((task.title + " " + task.description + " " + task.phase).lower().replace("/", " ").split())
        ranked = sorted(((len(tokens & set((m.skills + " " + m.role + " " + m.responsibilities).lower().replace(",", " ").split())), m) for m in members), key=lambda x: x[0], reverse=True)
        if not ranked or ranked[0][0] == 0: return {"task_id": task.id, "assignee": "", "rationale": "No explicit capability matches this task."}
        best = ranked[0][1]; return {"task_id": task.id, "assignee": best.name, "rationale": f"Based on listed skills/responsibilities: {best.skills or best.responsibilities}."}
    fallback = {"assignments": [choose(task) for task in tasks]}
    result = await ai.ask("Recommend an owner for each task based only on the supplied skills, responsibilities, and availability. Never assign someone without a matching stated capability. Return JSON {assignments:[{task_id,assignee,rationale}]}; use empty assignee when no safe match. Members and tasks: " + json.dumps({"members": [serialize(m) for m in members], "tasks": [serialize(t) for t in tasks]}, default=str), fallback, schemas.AssignmentOut)
    allowed_names = {m.name for m in members}; allowed_tasks = {t.id: t for t in tasks}
    for item in result["result"]["assignments"]:
        if item["task_id"] not in allowed_tasks or item["assignee"] not in allowed_names: item["assignee"] = ""; continue
        task = allowed_tasks[item["task_id"]]; task.assignee = item["assignee"]
    record(session, pid, "Task assignment recommendations applied"); session.commit()
    result["label"] = "Assignments use stated team profiles; review recommendations before work begins."
    return result

@app.get("/api/projects/{pid}/risks")
def risks(pid: int, session: Session = Depends(get_session)):
    p = get_project(session, pid); today = date.today(); result = []
    for task in p.tasks:
        if not task.assignee and task.status != "Completed": result.append({"title": "Unassigned task", "explanation": f"{task.title} has no owner.", "severity": "Medium", "action": "Assign a team member after reviewing their stated skills."})
        if task.due_date and task.due_date < today and task.status != "Completed": result.append({"title": "Overdue task", "explanation": f"{task.title} passed its due date.", "severity": "High", "action": "Reassess scope and update the deadline."})
        if not task.dependencies and task.phase in {"Core development", "Frontend integration", "Deployment"} and task.status != "Completed": result.append({"title": "Dependency not recorded", "explanation": f"{task.title} is in {task.phase} but has no dependencies recorded.", "severity": "Low", "action": "Confirm whether prerequisite work should be linked."})
    if not p.members: result.append({"title": "No team members", "explanation": "No team capacity has been recorded.", "severity": "Medium", "action": "Add team profiles to plan ownership."})
    if not p.tasks: result.append({"title": "Roadmap is empty", "explanation": "There are no tracked implementation tasks.", "severity": "High", "action": "Create tasks or generate a roadmap."})
    return {"mode": "rule_based_recommendations", "risks": result}

@app.post("/api/projects/{pid}/risks/analyze")
async def analyze_risks(pid: int, session: Session = Depends(get_session)):
    project = get_project(session, pid)
    fallback = risks(pid, session)
    result = await ai.ask("Review this project state for overdue work, missing assignments/dependencies, workload imbalance, absent phases, blockers, and submission risks. Return JSON {risks:[{title,explanation,severity,action}]}; do not claim inferred concerns are verified. Project: " + json.dumps({"project": serialize(project), "members": [serialize(m) for m in project.members], "tasks": [serialize(t) for t in project.tasks], "checks": [serialize(c) for c in project.checks]}, default=str)[:14000], fallback, schemas.RiskOut)
    result["label"] = "AI recommendations; verify against current project context." if result["mode"] == "ai" else "Rule-based recommendations; no AI provider configured."
    return result
