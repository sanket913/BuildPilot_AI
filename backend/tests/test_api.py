from fastapi.testclient import TestClient
from app.main import app
from app.config import Settings, settings
from pydantic import ValidationError

client = TestClient(app)

def project():
    response = client.post("/api/projects", json={"name": "Test workspace", "description": "Testing"})
    assert response.status_code == 200
    return response.json()["id"]

def test_health_and_fallback_analysis():
    assert client.get("/api/health").json()["status"] == "ok"
    result = client.post("/api/analyze", data={"text": "Accessible transit\nHelp riders plan routes"}).json()
    assert result["mode"] == "demo"
    assert result["result"]["summary"].startswith("Accessible transit")

def test_project_team_task_checklist_and_export():
    pid = project()
    member = client.post(f"/api/projects/{pid}/members", json={"name":"Ari", "role":"Developer", "skills":"Python"}).json()
    assert member["name"] == "Ari"
    task = client.post(f"/api/projects/{pid}/tasks", json={"title":"Build API", "assignee":"Ari"}).json()
    assert task["status"] == "To Do"
    task.update(status="Completed")
    assert client.patch(f"/api/tasks/{task['id']}", json=task).json()["status"] == "Completed"
    detail = client.get(f"/api/projects/{pid}").json()
    assert detail["members"][0]["skills"] == "Python"
    pending = detail["checks"][0]
    assert client.patch(f"/api/checks/{pending['id']}", json={"title":pending["title"],"done":True}).json()["done"] is True
    client.post(f"/api/projects/{pid}/documents", json={"title":"README.md","content":"# Test export"})
    assert client.get(f"/api/projects/{pid}/documentation.md").text == "# Test export"
    assert client.delete(f"/api/projects/{pid}").json()["ok"] is True

def test_missing_project_and_invalid_upload_errors():
    assert client.get("/api/projects/999999").status_code == 404
    assert client.post("/api/analyze", files={"file":("brief.exe",b"x")}).status_code == 415

def test_configured_workspace_access_gate(monkeypatch):
    monkeypatch.setattr(settings, "app_access_token", "test-workspace-secret-at-least-32-characters")
    assert client.get("/api/health").json()["access_controlled"] is True
    assert client.get("/api/projects").status_code == 401
    response = client.get("/api/projects", headers={"Authorization":"Bearer test-workspace-secret-at-least-32-characters"})
    assert response.status_code == 200
    preflight = client.options("/api/projects", headers={"Origin":"http://localhost:5173", "Access-Control-Request-Method":"GET"})
    assert preflight.status_code == 200

def test_project_input_rejects_unknown_status():
    response = client.post("/api/projects", json={"name":"Invalid status", "status":"Mystery"})
    assert response.status_code == 422

def test_production_configuration_requires_strong_access_code():
    try:
        Settings(app_env="production", app_access_token="short")
    except ValidationError:
        pass
    else:
        raise AssertionError("Production must reject a missing or weak access code")

def test_demo_generation_and_unconfigured_integration():
    assert client.get("/api/integrations/nonilion").json()["configured"] is False
    assert client.post("/api/solution", json={}).json()["mode"] == "demo"
    roadmap = client.post("/api/roadmap", json={}).json()
    assert roadmap["mode"] == "demo"
    assert len(roadmap["result"]["tasks"]) == 8
    assert all(task["acceptance_criteria"] and task["estimated_effort"] for task in roadmap["result"]["tasks"])

def test_project_analysis_roadmap_risk_documentation_and_archive():
    pid = client.post("/api/projects", json={"name":"Extended project", "hackathon_name":"Build weekend", "start_date":"2026-11-01", "deadline":"2026-11-20", "problem_statement":"Help local growers share harvests."}).json()["id"]
    analysis = client.post("/api/analyze", data={"project_id":str(pid), "text":"Help local growers share harvests."}).json()
    assert analysis["mode"] == "demo"
    assert client.get(f"/api/projects/{pid}").json()["analysis"]["title"]
    saved = client.put(f"/api/projects/{pid}/analysis", json={"problem_statement":"Help growers.", "analysis":analysis["result"]})
    assert saved.status_code == 200
    roadmap = client.post("/api/roadmap", json={"project_id":pid}).json()
    assert len(roadmap["result"]["tasks"]) >= 5
    detail = client.get(f"/api/projects/{pid}").json()
    assert len(detail["tasks"]) >= 5
    assert len({task["phase"] for task in detail["tasks"]}) >= 7
    assert client.get(f"/api/projects/{pid}/risks").status_code == 200
    doc = client.post(f"/api/projects/{pid}/documents/generate")
    assert doc.json()["mode"] == "demo"
    assert "# Extended project" in doc.json()["result"]["content"]
    assert client.post(f"/api/projects/{pid}/archive").json()["archived"] is True
    assert client.delete(f"/api/projects/{pid}").json()["ok"] is True

def test_sample_project_isolated_and_resettable():
    # Force a fresh fixture even when a developer database contains an older sample.
    assert client.delete("/api/demo").json()["ok"] is True
    seeded = client.post("/api/demo").json()
    sample_id = seeded["project_id"]
    detail = client.get(f"/api/projects/{sample_id}").json()
    assert detail["is_demo"] is True
    assert len(detail["members"]) == 4
    assert len(detail["tasks"]) >= 8
    assert len({task["phase"] for task in detail["tasks"]}) == 8
    assert {task["status"] for task in detail["tasks"]} == {"To Do", "In Progress", "Review", "Completed"}
    assert any(not task["assignee"] for task in detail["tasks"])
    assert len(detail["activities"]) >= 4
    assert 0 < sum(1 for check in detail["checks"] if check["done"]) < len(detail["checks"])
    assert any(doc["title"] == "README.md" for doc in detail["documents"])
    assert client.get("/api/demo").json()["available"] is True
    risk_result = client.post(f"/api/projects/{sample_id}/risks/analyze").json()
    assert risk_result["mode"] == "demo"
    assert risk_result["result"]["risks"]
    assignments = client.post(f"/api/projects/{sample_id}/allocate").json()
    assert assignments["result"]["assignments"]
    assert client.delete("/api/demo").json()["ok"] is True
    assert client.get(f"/api/projects/{sample_id}").status_code == 404
