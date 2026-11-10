from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    description: str = Field(default="", max_length=10000)
    hackathon_name: str = Field(default="", max_length=180)
    start_date: date | None = None
    deadline: date | None = None
    status: Literal["Planning", "In Progress", "At Risk", "Submitted", "Completed"] = "Planning"
    problem_statement: str = Field(default="", max_length=100000)


class MemberIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    role: str = Field(default="Team member", max_length=100)
    skills: str = Field(default="", max_length=2000)
    availability: str = Field(default="Flexible", max_length=80)
    experience_level: str = Field(default="Not specified", max_length=40)
    responsibilities: str = Field(default="", max_length=2000)


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    status: Literal["To Do", "In Progress", "Review", "Completed"] = "To Do"
    priority: Literal["Low", "Medium", "High", "Critical"] = "Medium"
    assignee: str = Field(default="", max_length=100)
    due_date: date | None = None
    phase: str = Field(default="Core development", max_length=100)
    dependencies: str = Field(default="", max_length=4000)
    acceptance_criteria: str = Field(default="", max_length=4000)
    estimated_effort: str = Field(default="", max_length=40)


class CheckIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    done: bool = False


class DocIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(max_length=250000)


class AnalysisOut(BaseModel):
    title: str
    summary: str
    objective: str
    domain: str
    target_users: list[str] = Field(default_factory=list)
    functional_requirements: list[str] = Field(default_factory=list)
    non_functional_requirements: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    evaluation_criteria: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recommendation: str
    confidence_note: str = "AI-generated; verify against source brief."


class AnalysisSave(BaseModel):
    problem_statement: str = Field(max_length=100000)
    analysis: AnalysisOut


class SolutionOut(BaseModel):
    name: str
    summary: str
    approach: str
    features: list[str]
    architecture: str
    stack: list[str]
    ai_components: list[str] = Field(default_factory=list)
    data_design: str
    api_design: str
    phases: list[str]
    impact: str
    limitations: list[str]


class SolutionSave(BaseModel):
    solution: SolutionOut


class AssignmentItem(BaseModel):
    task_id: int
    assignee: str = ""
    rationale: str


class AssignmentOut(BaseModel):
    assignments: list[AssignmentItem]


class RoadmapTask(BaseModel):
    title: str
    description: str
    phase: str
    priority: Literal["Low", "Medium", "High", "Critical"] = "Medium"
    status: Literal["To Do", "In Progress", "Review", "Completed"] = "To Do"
    assignee: str = ""
    dependencies: list[str] = Field(default_factory=list)
    acceptance_criteria: str = ""
    estimated_effort: str = ""
    due_date: date | None = None


class RoadmapOut(BaseModel):
    tasks: list[RoadmapTask]


class RiskItem(BaseModel):
    title: str
    explanation: str
    severity: Literal["Low", "Medium", "High", "Critical"]
    action: str


class RiskOut(BaseModel):
    risks: list[RiskItem]


class TextOut(BaseModel):
    content: str
