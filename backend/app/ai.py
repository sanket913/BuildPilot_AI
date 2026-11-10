import json
import logging
import httpx
from pydantic import BaseModel
from .config import settings

logger = logging.getLogger("buildpilot.ai")

async def ask(prompt: str, fallback, schema: type[BaseModel] | None = None):
    if not settings.ai_api_key:
        return {"mode": "demo", "result": fallback}
    try:
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            response = await client.post(
                settings.ai_base_url.rstrip("/") + "/chat/completions",
                headers={"Authorization": f"Bearer {settings.ai_api_key}"},
                json={"model": settings.ai_model, "response_format": {"type": "json_object"},
                      "messages": [{"role": "system", "content": "Return valid JSON only. Do not invent facts; distinguish recommendations."},
                                   {"role": "user", "content": prompt}]})
            response.raise_for_status()
            result = json.loads(response.json()["choices"][0]["message"]["content"])
            if not isinstance(result, dict):
                raise ValueError("AI response must be a JSON object")
            if schema:
                result = schema.model_validate(result).model_dump(mode="json")
            return {"mode": "ai", "result": result}
    except Exception as exc:
        logger.warning("AI provider request failed (%s); returning labeled fallback guidance", type(exc).__name__)
        if schema:
            fallback = schema.model_validate(fallback).model_dump(mode="json")
        return {"mode": "demo", "warning": f"AI response was unavailable or invalid ({type(exc).__name__}); showing labelled demo guidance.", "result": fallback}

def analyze_fallback(text: str):
    lines = [line.strip(" -# ") for line in text.splitlines() if line.strip()]
    return {"title": lines[0][:120] if lines else "Untitled challenge", "summary": text[:700],
            "objective": "Review the brief and define a measurable outcome.", "domain": "To be confirmed from brief",
            "target_users": [], "functional_requirements": [], "non_functional_requirements": [],
            "constraints": [], "deliverables": [], "evaluation_criteria": [], "risks": [],
            "missing_information": ["Target users", "Success metrics", "Technical or time constraints"],
            "recommendation": "Convert the challenge into a small testable prototype.",
            "source_note": "Demo summary uses supplied text; other fields are recommendations, not extracted facts."}
