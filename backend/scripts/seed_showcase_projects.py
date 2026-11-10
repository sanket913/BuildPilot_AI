"""Seed three realistic, self-contained workspaces for a BuildPilot demo.

Run from the backend directory with:
    .venv/Scripts/python scripts/seed_showcase_projects.py

The script is idempotent by project name and only inserts missing showcases.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import db


CHECKLIST = [
    "Problem statement analyzed",
    "Solution finalized",
    "Architecture documented",
    "Core functionality implemented",
    "Frontend completed",
    "Backend completed",
    "AI integration tested",
    "Application tested",
    "GitHub repository prepared",
    "Deployment verified",
    "README completed",
    "Presentation prepared",
    "Demo tested",
]


SHOWCASES = [
    {
        "name": "NightOwl Routes",
        "description": "A safer late-night campus travel companion that helps students choose well-lit routes and coordinate trusted check-ins.",
        "hackathon_name": "Campus Safety Buildathon",
        "status": "In Progress",
        "days_until": 4,
        "statement": "Students walking across campus after dark often cannot tell which paths are well-lit, open, or under construction. Design a privacy-conscious way to help people plan a safer route and let a trusted contact know they arrived.",
        "analysis": {
            "title": "Safer late-night campus travel",
            "summary": "Students need current, understandable route information after dark, including lighting and temporary closures.",
            "objective": "Help a student compare available campus routes and optionally share an arrival check-in with a trusted contact.",
            "domain": "Campus safety and mobility",
            "target_users": ["Students walking after dark", "Campus safety staff", "Facilities teams"],
            "functional_requirements": ["Show campus paths and entrances", "Mark lighting concerns and closures", "Compare route options", "Offer an opt-in arrival check-in"],
            "non_functional_requirements": ["Work on a mobile screen", "Minimize collection of location data", "Clearly label community reports and their age"],
            "constraints": ["No access to live campus lighting sensors", "Route data must be supplied or reviewed by the campus", "Emergency services integration is out of scope"],
            "deliverables": ["Interactive campus route prototype", "Report review workflow", "Privacy and safety notes"],
            "evaluation_criteria": ["Route comparison is understandable", "Stale or unverified reports are clearly identified", "Check-in is optional"],
            "risks": ["Unverified reports could mislead users", "Location sharing can expose sensitive movement"],
            "missing_information": ["Campus map data source", "Who moderates reports", "Retention period for check-in data"],
            "recommendation": "Demonstrate route comparison on a small sample campus map and label every condition report with its source and timestamp.",
            "confidence_note": "Seeded demo brief for product walkthrough; verify campus policies and map data before real deployment.",
        },
        "solution": {
            "name": "NightOwl Routes",
            "summary": "A mobile-first campus map that compares paths using campus-reviewed lighting and closure notes, with an optional trusted-contact arrival check-in.",
            "approach": "Use a clearly labeled sample map for the prototype. Students compare two routes, inspect when reports were submitted, and choose whether to start an arrival check-in.",
            "features": ["Campus route comparison", "Timestamped lighting and closure reports", "Campus staff review queue", "Optional arrival check-in"],
            "architecture": "React map interface, FastAPI route and report API, PostgreSQL-ready campus path and report records.",
            "stack": ["React", "TypeScript", "FastAPI", "PostgreSQL", "OpenStreetMap-compatible map layer"],
            "ai_components": ["Optional plain-language summary of route reports; never used to claim a path is safe"],
            "data_design": "Campus paths, entrances, condition reports, review decisions, and user-controlled check-in records.",
            "api_design": "Read route options; create condition reports; review reports; create and expire opt-in check-ins.",
            "phases": ["Map and user research", "Route data model", "Comparison interface", "Report review", "Privacy review and demo"],
            "impact": "Evaluate route comparison completion and report review time with campus partners; do not claim safety outcomes without a study.",
            "limitations": ["Prototype map is not an emergency service", "Sample reports are not verified live conditions", "Check-in retention and consent need campus review"],
        },
        "members": [
            ("Anaya Mehta", "Product designer", "UX research, Figma, accessibility", "Interview students and shape the route flow"),
            ("Kabir Shah", "Frontend engineer", "React, TypeScript, maps, CSS", "Build the map and mobile route comparison"),
            ("Riya Nair", "Backend engineer", "Python, FastAPI, PostgreSQL", "Implement route and report endpoints"),
            ("Arjun Rao", "Safety and data lead", "GIS, data modeling, privacy review", "Prepare sample map data and review privacy assumptions"),
        ],
        "tasks": [
            ("Map the late-night journey", "Define the student flow from route selection through optional arrival check-in.", "Completed", "High", "Anaya Mehta", "Research and planning", 0, "The team reviews one agreed primary user journey.", "2 hours", ""),
            ("Create sample campus path data", "Model paths, entrances, lighting notes, and temporary closures for a small demo area.", "Completed", "High", "Arjun Rao", "Architecture and setup", 0, "Every sample route record has a source label and timestamp.", "3 hours", "Map the late-night journey"),
            ("Build route comparison screen", "Show two route options with distance and available condition notes.", "In Progress", "Critical", "Kabir Shah", "Core development", 1, "A user can compare two sample paths on mobile.", "5 hours", "Create sample campus path data"),
            ("Implement report review endpoint", "Allow staff to mark a condition report reviewed or outdated.", "Review", "High", "Riya Nair", "Core development", 1, "Review state and reviewer timestamp persist after reload.", "4 hours", "Create sample campus path data"),
            ("Add optional arrival check-in", "Create a consent-first check-in flow with a clear expiry time.", "To Do", "High", "Riya Nair", "Core development", 2, "Check-in is opt-in and expires at the stated time.", "4 hours", "Build route comparison screen"),
            ("Label report confidence and age", "Make unverified reports and stale conditions visually distinct.", "To Do", "Critical", "Anaya Mehta", "Frontend and backend integration", 2, "No report is presented as verified campus safety data.", "3 hours", "Implement report review endpoint"),
            ("Review privacy and emergency wording", "Check location, consent, retention, and safety language with a campus stakeholder.", "To Do", "Critical", "Arjun Rao", "Testing and debugging", 3, "The demo states its limits and explains check-in retention.", "2 hours", "Add optional arrival check-in"),
            ("Prepare judge demo and deployment", "Deploy the prototype and rehearse route comparison with sample map data.", "To Do", "Medium", "Kabir Shah", "Presentation and submission", 4, "A judge can complete the demo without a live campus integration.", "3 hours", "Label report confidence and age"),
        ],
        "checks_done": {0, 1, 2, 10},
    },
    {
        "name": "CareBridge Queue",
        "description": "An offline-friendly community clinic check-in and queue display designed around clear language and patient privacy.",
        "hackathon_name": "Health Access Innovation Jam",
        "status": "In Progress",
        "days_until": 6,
        "statement": "Small community clinics rely on paper queues and verbal updates. Visitors may not know where they are in line or what documents to prepare, while staff have limited time to answer repeated status questions. Create a simple check-in and queue experience without exposing sensitive health details.",
        "analysis": {
            "title": "Clearer community clinic visits",
            "summary": "Visitors need understandable check-in and queue updates, while clinic staff need a low-effort way to manage the waiting room.",
            "objective": "Prototype a privacy-conscious queue display and check-in workflow for a community clinic.",
            "domain": "Community health access",
            "target_users": ["Clinic visitors", "Front-desk staff", "Volunteer coordinators"],
            "functional_requirements": ["Issue a non-identifying queue token", "Show approximate queue position", "Display preparation instructions", "Allow staff to advance or pause a queue item"],
            "non_functional_requirements": ["Readable on a shared tablet", "Support low-connectivity conditions", "Avoid displaying patient names or diagnoses"],
            "constraints": ["No electronic health record integration", "Queue timing is an estimate", "Use synthetic data for the demo"],
            "deliverables": ["Visitor check-in prototype", "Staff queue panel", "Privacy review notes"],
            "evaluation_criteria": ["Visitors can understand their next step", "Staff can update the queue quickly", "Shared display reveals no sensitive details"],
            "risks": ["Estimated wait times can change", "A visible token may still be identifying in a small clinic"],
            "missing_information": ["Clinic language requirements", "Queue retention policy", "Accessibility needs of the pilot site"],
            "recommendation": "Prototype with synthetic queue records and test wording with clinic staff before connecting to real patient workflows.",
            "confidence_note": "Seeded demo brief; not a clinical system and not connected to patient records.",
        },
        "solution": {
            "name": "CareBridge Queue",
            "summary": "A lightweight clinic check-in flow that issues a temporary queue token and gives staff a simple, privacy-aware waiting-room board.",
            "approach": "Use synthetic visitors in the demo. Visitors receive a temporary token and preparation instructions; staff update queue states from a separate panel.",
            "features": ["Temporary check-in token", "Staff queue controls", "Estimated wait range with uncertainty note", "Plain-language preparation steps"],
            "architecture": "Responsive web client with an offline-tolerant local queue view, FastAPI service, and relational queue records.",
            "stack": ["React", "TypeScript", "FastAPI", "SQLite for demo", "PostgreSQL for hosted deployment"],
            "ai_components": ["Optional translation draft for clinic-reviewed instructions; no diagnosis or triage"],
            "data_design": "Temporary queue token, queue state, created time, and clinic-reviewed instruction templates; no names or diagnosis in the public board.",
            "api_design": "Create a temporary queue entry; read a token status; advance, pause, or complete an entry; expire old demo records.",
            "phases": ["Clinic workflow discovery", "Privacy-first queue model", "Visitor check-in", "Staff controls", "Usability and offline review"],
            "impact": "Measure check-in completion and staff update time during a supervised usability session.",
            "limitations": ["Not an electronic health record", "Wait ranges are estimates", "Real clinic use requires privacy and accessibility review"],
        },
        "members": [
            ("Tara Joseph", "Service designer", "Service design, interviews, plain language", "Map clinic visitor and staff needs"),
            ("Neil Fernandes", "Frontend developer", "React, TypeScript, accessibility", "Build visitor check-in and queue display"),
            ("Sana Iqbal", "Backend developer", "Python, FastAPI, SQL", "Create temporary queue API and expiry rules"),
            ("Vihaan Kulkarni", "Research and QA", "Usability testing, localization, testing", "Test instructions and synthetic scenarios"),
        ],
        "tasks": [
            ("Document visitor check-in flow", "Map the minimum steps from arrival to receiving a queue token.", "Completed", "High", "Tara Joseph", "Research and planning", 0, "Staff and visitor flows are documented separately.", "2 hours", ""),
            ("Define temporary queue record", "Create a schema that avoids personal health details and expires demo records.", "Completed", "Critical", "Sana Iqbal", "Architecture and setup", 0, "Queue data contains no name or diagnosis fields.", "3 hours", "Document visitor check-in flow"),
            ("Build visitor token screen", "Issue a readable temporary token and show preparation instructions.", "In Progress", "High", "Neil Fernandes", "Core development", 1, "A visitor can finish check-in using synthetic data.", "4 hours", "Define temporary queue record"),
            ("Implement staff queue controls", "Allow staff to advance, pause, and complete a queue entry.", "Review", "Critical", "Sana Iqbal", "Core development", 1, "Queue transitions persist and are visible on the board.", "4 hours", "Define temporary queue record"),
            ("Add offline-friendly queue view", "Keep the current synthetic queue readable during a brief connection loss.", "To Do", "Medium", "Neil Fernandes", "Frontend and backend integration", 2, "The last synced queue view remains clearly labeled as stale.", "3 hours", "Build visitor token screen"),
            ("Review plain-language instructions", "Test the preparation copy with a non-clinical reader and clinic advisor.", "To Do", "High", "Tara Joseph", "Testing and debugging", 3, "Instructions are understandable and clinic-approved for the demo.", "2 hours", "Build visitor token screen"),
            ("Run privacy and accessibility checks", "Check token visibility, keyboard flow, contrast, and shared-display content.", "To Do", "Critical", "Vihaan Kulkarni", "Testing and debugging", 4, "Shared display exposes no personal health information.", "3 hours", "Implement staff queue controls"),
            ("Rehearse clinic demo", "Walk through visitor and staff views using synthetic records.", "To Do", "Medium", "Vihaan Kulkarni", "Presentation and submission", 5, "The demo communicates that wait time is an estimate.", "2 hours", "Run privacy and accessibility checks"),
        ],
        "checks_done": {0, 1, 2, 4, 10},
    },
    {
        "name": "CivicLens",
        "description": "A neighborhood issue-reporting prototype that helps residents submit accessible reports and helps civic teams triage them transparently.",
        "hackathon_name": "Open City Civic Tech Challenge",
        "status": "Planning",
        "days_until": 8,
        "statement": "Residents often do not know where to report broken streetlights, blocked sidewalks, or overflowing bins, and they rarely receive a clear update. Build a transparent prototype that routes reports to the right civic team while protecting reporter privacy and avoiding promises about repair timelines.",
        "analysis": {
            "title": "Make neighborhood reports easier to follow",
            "summary": "Residents need a clear reporting path and meaningful status updates for common public-space issues.",
            "objective": "Prototype an accessible reporting and triage workflow for a small, clearly bounded set of civic issue types.",
            "domain": "Civic technology and public services",
            "target_users": ["Residents", "Community organizations", "Civic operations teams"],
            "functional_requirements": ["Submit an issue with category and location", "Attach an optional image", "Route reports to a team queue", "Show status changes and public updates"],
            "non_functional_requirements": ["Accessible on mobile", "Allow reports without a public name", "Explain what location and image data are stored"],
            "constraints": ["No live municipal dispatch connection", "Demo uses a sample neighborhood map", "Repair timelines cannot be guaranteed"],
            "deliverables": ["Resident report form", "Triage dashboard", "Public status page", "Data and moderation notes"],
            "evaluation_criteria": ["A report is easy to submit", "Staff can triage by category", "Status language does not promise completion"],
            "risks": ["Duplicate or inaccurate reports", "Images may reveal personal information", "Unmoderated public comments can be harmful"],
            "missing_information": ["Official category and routing list", "Image retention policy", "Moderation owner and service-level expectations"],
            "recommendation": "Start with three categories and an internal triage queue; show residents only statuses confirmed by the civic team.",
            "confidence_note": "Seeded demo brief; routing and status updates are simulated until an official civic service is verified.",
        },
        "solution": {
            "name": "CivicLens",
            "summary": "An accessible issue-reporting flow paired with a triage workspace that gives residents clear, verified status updates.",
            "approach": "Use a sample neighborhood and three issue categories. Reports enter a staff queue; only reviewed status updates appear on the public tracking view.",
            "features": ["Mobile issue report form", "Optional redacted image upload", "Staff category and duplicate triage", "Public status timeline"],
            "architecture": "React resident portal and triage board, FastAPI report service, relational issue records, and a map layer over sample geography.",
            "stack": ["React", "TypeScript", "FastAPI", "PostgreSQL", "OpenStreetMap-compatible map layer"],
            "ai_components": ["Optional category suggestion for staff review; never auto-dispatch reports"],
            "data_design": "Issue category, approximate location, optional image reference, moderation state, staff queue, and verified public updates.",
            "api_design": "Create a report; list reports for staff triage; update internal status; publish a reviewed resident-facing update.",
            "phases": ["Select pilot issue categories", "Design resident report flow", "Build staff triage queue", "Add public status page", "Moderation and demo review"],
            "impact": "Evaluate submission completion and triage time in a prototype test; do not claim faster repairs without municipal data.",
            "limitations": ["No live city service integration", "Sample locations are illustrative", "Public updates require moderation"],
        },
        "members": [
            ("Zoya Desai", "Civic product lead", "Community research, service design, writing", "Confirm reporting flow and public status language"),
            ("Ethan D'Souza", "Frontend engineer", "React, TypeScript, maps, accessibility", "Build the report form and map view"),
            ("Meera Kapoor", "Backend engineer", "Python, FastAPI, PostgreSQL", "Build report storage and staff triage endpoints"),
            ("Rehan Ali", "Trust and data lead", "Data privacy, moderation, QA", "Define image handling and moderation rules"),
        ],
        "tasks": [
            ("Choose the first three report types", "Bound the demo to streetlight, sidewalk obstruction, and overflowing bin reports.", "Completed", "High", "Zoya Desai", "Research and planning", 0, "Each category has a clear example and routing owner.", "2 hours", ""),
            ("Sketch resident report and tracking flow", "Show how a resident submits a report and checks its reviewed status.", "In Progress", "High", "Zoya Desai", "Research and planning", 1, "A report can be followed without publishing a reporter name.", "3 hours", "Choose the first three report types"),
            ("Create sample neighborhood map", "Prepare fictional locations and boundaries for the presentation.", "To Do", "Medium", "Ethan D'Souza", "Architecture and setup", 2, "Every map marker is labeled as demo data.", "3 hours", "Choose the first three report types"),
            ("Implement report submission endpoint", "Validate category, approximate location, and optional image metadata.", "To Do", "Critical", "Meera Kapoor", "Core development", 3, "A report is stored with a moderation state and no public identity.", "5 hours", "Sketch resident report and tracking flow"),
            ("Build staff triage workspace", "Let staff review category, duplicate candidates, and report status.", "To Do", "High", "Ethan D'Souza", "Core development", 4, "Staff can review and update a report state.", "5 hours", "Implement report submission endpoint"),
            ("Add verified resident status timeline", "Expose only reviewed updates on the tracking page.", "To Do", "High", "Meera Kapoor", "Frontend and backend integration", 5, "Draft internal notes never appear as public updates.", "4 hours", "Build staff triage workspace"),
            ("Review image and moderation safeguards", "Document image retention, redaction, and abusive-report handling.", "To Do", "Critical", "Rehan Ali", "Testing and debugging", 6, "The demo states who can view an uploaded image and for how long.", "3 hours", "Implement report submission endpoint"),
            ("Prepare civic challenge presentation", "Rehearse the resident and staff flows using fictional sample reports.", "To Do", "Medium", "Zoya Desai", "Presentation and submission", 7, "Presentation distinguishes prototype behavior from real city integration.", "2 hours", "Add verified resident status timeline"),
        ],
        "checks_done": {0, 1},
    },
]


def seed_one(session, item: dict) -> bool:
    if session.query(db.Project).filter_by(name=item["name"]).first():
        return False

    today = date.today()
    project = db.Project(
        name=item["name"],
        description=item["description"],
        hackathon_name=item["hackathon_name"],
        start_date=today,
        deadline=today + timedelta(days=item["days_until"]),
        status=item["status"],
        is_demo=False,
        problem_statement=item["statement"],
        analysis=json.dumps(item["analysis"]),
        solution=json.dumps(item["solution"]),
    )
    session.add(project)
    session.flush()

    members = []
    for name, role, skills, responsibilities in item["members"]:
        member = db.Member(
            project_id=project.id,
            name=name,
            role=role,
            skills=skills,
            responsibilities=responsibilities,
            experience_level="Intermediate",
            availability="8 hours / week",
        )
        session.add(member)
        members.append(name)

    for (title, description, status, priority, assignee, phase, due_in,
         criteria, effort, dependencies) in item["tasks"]:
        session.add(db.Task(
            project_id=project.id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            assignee=assignee,
            phase=phase,
            due_date=today + timedelta(days=due_in),
            acceptance_criteria=criteria,
            estimated_effort=effort,
            dependencies=dependencies,
        ))

    for index, title in enumerate(CHECKLIST):
        session.add(db.Check(project_id=project.id, title=title, done=index in item["checks_done"]))

    readme = (
        f"# {item['name']}\n\n{item['description']}\n\n"
        f"## Challenge\n\n{item['statement']}\n\n"
        f"## Proposed solution\n\n{item['solution']['summary']}\n\n"
        f"## Demo boundaries\n\n"
        + "\n".join(f"- {limitation}" for limitation in item["solution"]["limitations"])
        + "\n\n## Local development\n\nStart the FastAPI backend and Vite frontend in separate terminals.\n"
    )
    session.add(db.Document(project_id=project.id, title="README.md", content=readme))
    session.flush()

    for message in [
        "Showcase workspace created",
        "Challenge analysis and proposal prepared for demo",
        f"{len(members)} demo team profiles added",
        f"{len(item['tasks'])} roadmap tasks added with mixed statuses",
        "Submission checklist and README prepared",
    ]:
        session.add(db.Activity(project_id=project.id, message=message, created_at=datetime.utcnow()))
    return True


def main() -> None:
    db.init_db()
    with db.SessionLocal() as session:
        added = [item["name"] for item in SHOWCASES if seed_one(session, item)]
        session.commit()
        existing = [(project.id, project.name) for project in session.query(db.Project).order_by(db.Project.id)]
    if added:
        print("Created showcase workspaces:")
        for name in added:
            print(f"  - {name}")
    else:
        print("All showcase workspaces already exist; no duplicates created.")
    print("Workspaces in database:")
    for project_id, name in existing:
        print(f"  {project_id}: {name}")


if __name__ == "__main__":
    main()
