from dataclasses import dataclass
from typing import Protocol

class NonilionAdapter(Protocol):
    """Contract to implement only after verified Nonilion API docs are supplied."""
    async def connection_status(self) -> dict: ...
    async def interact(self, agent_input: dict) -> dict: ...

@dataclass
class UnconfiguredNonilion:
    async def connection_status(self) -> dict:
        return {"configured": False, "message": "No verified Nonilion API specification is available."}

    async def interact(self, agent_input: dict) -> dict:
        return {"configured": False, "message": "Agent calls are unavailable until verified Nonilion API documentation and credentials are provided."}

adapter: NonilionAdapter = UnconfiguredNonilion()
