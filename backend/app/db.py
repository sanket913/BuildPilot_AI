from datetime import datetime, date
from sqlalchemy import create_engine, String, Text, Date, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy import inspect, text as sql_text
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship, sessionmaker
from .config import settings

url = settings.database_url
if url.startswith("postgres://"):
    url = "postgresql+psycopg://" + url[len("postgres://"):]
elif url.startswith("postgresql://"):
    url = "postgresql+psycopg://" + url[len("postgresql://"):]
engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {}, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase): pass

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), default="My hackathon project")
    description: Mapped[str] = mapped_column(Text, default="")
    hackathon_name: Mapped[str] = mapped_column(String(180), default="")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="Planning")
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    problem_statement: Mapped[str] = mapped_column(Text, default="")
    analysis: Mapped[str] = mapped_column(Text, default="")
    solution: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    members: Mapped[list["Member"]] = relationship(cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship(cascade="all, delete-orphan")
    checks: Mapped[list["Check"]] = relationship(cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(cascade="all, delete-orphan")
    activities: Mapped[list["Activity"]] = relationship(cascade="all, delete-orphan")

class Member(Base):
    __tablename__ = "members"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(100), default="Team member")
    skills: Mapped[str] = mapped_column(Text, default="")
    availability: Mapped[str] = mapped_column(String(80), default="Flexible")
    experience_level: Mapped[str] = mapped_column(String(40), default="Not specified")
    responsibilities: Mapped[str] = mapped_column(Text, default="")

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="To Do")
    priority: Mapped[str] = mapped_column(String(20), default="Medium")
    assignee: Mapped[str] = mapped_column(String(100), default="")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    phase: Mapped[str] = mapped_column(String(100), default="Core development")
    dependencies: Mapped[str] = mapped_column(Text, default="")
    acceptance_criteria: Mapped[str] = mapped_column(Text, default="")
    estimated_effort: Mapped[str] = mapped_column(String(40), default="")

class Check(Base):
    __tablename__ = "checks"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String(200))
    done: Mapped[bool] = mapped_column(Boolean, default=False)

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    message: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(engine)
    additions = {
        "projects": {"hackathon_name": "VARCHAR(180) NOT NULL DEFAULT ''", "start_date": "DATE", "deadline": "DATE", "status": "VARCHAR(30) NOT NULL DEFAULT 'Planning'", "archived": "BOOLEAN NOT NULL DEFAULT FALSE", "is_demo": "BOOLEAN NOT NULL DEFAULT FALSE", "problem_statement": "TEXT NOT NULL DEFAULT ''", "analysis": "TEXT NOT NULL DEFAULT ''", "solution": "TEXT NOT NULL DEFAULT ''"},
        "members": {"experience_level": "VARCHAR(40) NOT NULL DEFAULT 'Not specified'", "responsibilities": "TEXT NOT NULL DEFAULT ''"},
        "tasks": {"acceptance_criteria": "TEXT NOT NULL DEFAULT ''", "estimated_effort": "VARCHAR(40) NOT NULL DEFAULT ''"},
    }
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table, columns in additions.items():
            present = {column["name"] for column in inspector.get_columns(table)}
            for column, declaration in columns.items():
                if column not in present:
                    connection.execute(sql_text(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}"))
