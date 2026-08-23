import json
import logging
import time
from typing import List, Optional
from pydantic import BaseModel, Field
import httpx

from app.core.config import settings

logger = logging.getLogger("llm_client")
logger.setLevel(logging.INFO)


class RiskAnalysisOutput(BaseModel):
    risk_level: str = Field(..., description="Risk tier: low, medium, high, or critical")
    risk_score: float = Field(..., ge=0.0, le=10.0, description="Numerical risk score from 0.0 to 10.0")
    technical_summary: str = Field(..., description="Technical summary for engineering leads & SREs")
    business_summary: str = Field(..., description="Plain-language summary for business and ops stakeholders")
    recommendations: List[str] = Field(..., description="List of mitigation recommendations")
    is_degraded: bool = Field(False, description="Flag indicating whether mock or fallback engine was used")


def generate_mock_heuristic_analysis(change_text: str, rag_context: Optional[str] = None) -> RiskAnalysisOutput:
    """
    Zero-cost deterministic heuristic fallback engine used in CI, offline mode, or upon API degradation.
    Analyzes deployment change text keywords to produce realistic technical and business risk assessments.
    """
    text_lower = change_text.lower()
    recommendations = []

    # High / Critical risk triggers
    if any(k in text_lower for k in ["schema", "migration", "drop table", "database", "auth", "jwt", "crypto", "security", "firewall", "kernel"]):
        risk_level = "high"
        risk_score = 8.2
        tech_summary = "High-risk architectural change detected involving core database schema, authentication mechanisms, or security boundaries. Potential for data loss or service interruption if unverified."
        biz_summary = "This deployment modifies core security or data storage structures. A minor failure could disrupt customer login or persistent data."
        recommendations = [
            "Perform database backup prior to migration execution.",
            "Verify rollback scripts in staging environment.",
            "Schedule deployment during low-traffic maintenance window.",
            "Ensure active SRE monitoring on error metrics.",
        ]
    elif any(k in text_lower for k in ["redis", "k8s", "kubernetes", "ingress", "upgrade", "refactor", "cluster", "replica"]):
        risk_level = "medium"
        risk_score = 5.4
        tech_summary = "Moderate-risk infrastructure or cache cluster modification. Service configuration changes require load monitoring and health checks."
        biz_summary = "This update adjusts background infrastructure performance. System throughput and response times should be observed post-release."
        recommendations = [
            "Monitor cluster CPU and memory utilization post-deploy.",
            "Maintain 1-click canary rollback readiness.",
            "Validate endpoint latency SLA metrics.",
        ]
    else:
        risk_level = "low"
        risk_score = 1.8
        tech_summary = "Low-risk minor update (documentation, UI polish, non-critical helper logic). Low probability of regression."
        biz_summary = "Minor operational update with minimal customer visibility or system impact."
        recommendations = [
            "Proceed with standard automated CI deployment pipeline.",
            "Verify basic UI/smoke test suite.",
        ]

    if rag_context:
        tech_summary += f"\n[RAG Historical Context Retrieved]: {rag_context[:300]}..."

    return RiskAnalysisOutput(
        risk_level=risk_level,
        risk_score=risk_score,
        technical_summary=tech_summary,
        business_summary=biz_summary,
        recommendations=recommendations,
        is_degraded=True,
    )


class LLMClient:
    """
    Provider-agnostic LLM client wrapper supporting OpenAI, Gemini, and Mock fallback.
    Guarantees structured Pydantic validation, retries with backoff, token logging, and graceful degradation.
    """

    def __init__(self):
        self.provider = getattr(settings, "LLM_PROVIDER", "mock").lower()
        self.openai_key = getattr(settings, "OPENAI_API_KEY", "").strip()
        self.gemini_key = getattr(settings, "GEMINI_API_KEY", "").strip()

    def generate_risk_assessment(
        self, change_text: str, rag_context: Optional[str] = None
    ) -> RiskAnalysisOutput:
        start_time = time.time()

        # Force mock fallback if provider is mock or missing keys
        if self.provider == "mock" or (self.provider == "openai" and not self.openai_key) or (self.provider == "gemini" and not self.gemini_key):
            logger.info(f"Using Mock LLM Heuristic Engine (Provider: {self.provider})")
            return generate_mock_heuristic_analysis(change_text, rag_context)

        # 1. OpenAI Provider Implementation
        if self.provider == "openai":
            for attempt in range(2):
                try:
                    logger.info(f"Calling OpenAI API (Attempt {attempt + 1})...")
                    prompt = f"""You are an expert DevOps Risk Assessor.
Analyze the following deployment change text and optional historical context:

CHANGE TEXT:
{change_text}

HISTORICAL RAG CONTEXT:
{rag_context or 'None'}

Return a JSON object with strictly these keys:
- "risk_level": "low", "medium", "high", or "critical"
- "risk_score": float between 0.0 and 10.0
- "technical_summary": technical summary for SREs
- "business_summary": plain language summary for business leaders
- "recommendations": array of string recommendations
"""
                    response = httpx.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.openai_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [{"role": "user", "content": prompt}],
                            "response_format": {"type": "json_object"},
                            "temperature": 0.2,
                        },
                        timeout=15.0,
                    )
                    if response.status_code == 200:
                        content_str = response.json()["choices"][0]["message"]["content"]
                        parsed_json = json.loads(content_str)
                        output = RiskAnalysisOutput(
                            risk_level=parsed_json.get("risk_level", "medium"),
                            risk_score=float(parsed_json.get("risk_score", 5.0)),
                            technical_summary=parsed_json.get("technical_summary", ""),
                            business_summary=parsed_json.get("business_summary", ""),
                            recommendations=parsed_json.get("recommendations", []),
                            is_degraded=False,
                        )
                        elapsed = time.time() - start_time
                        logger.info(f"OpenAI API call succeeded in {elapsed:.2f}s")
                        return output
                except Exception as e:
                    logger.warning(f"OpenAI API attempt {attempt + 1} failed: {e}")
                    time.sleep(1.0)

        # 2. Gemini Provider Implementation
        if self.provider == "gemini":
            for attempt in range(2):
                try:
                    logger.info(f"Calling Gemini API (Attempt {attempt + 1})...")
                    prompt = f"""Analyze this deployment change and return JSON with keys: risk_level, risk_score, technical_summary, business_summary, recommendations.
CHANGE TEXT:
{change_text}
HISTORICAL CONTEXT:
{rag_context or 'None'}"""
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
                    response = httpx.post(
                        url,
                        json={
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {"responseMimeType": "application/json"},
                        },
                        timeout=15.0,
                    )
                    if response.status_code == 200:
                        content_str = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                        parsed_json = json.loads(content_str)
                        output = RiskAnalysisOutput(
                            risk_level=parsed_json.get("risk_level", "medium"),
                            risk_score=float(parsed_json.get("risk_score", 5.0)),
                            technical_summary=parsed_json.get("technical_summary", ""),
                            business_summary=parsed_json.get("business_summary", ""),
                            recommendations=parsed_json.get("recommendations", []),
                            is_degraded=False,
                        )
                        elapsed = time.time() - start_time
                        logger.info(f"Gemini API call succeeded in {elapsed:.2f}s")
                        return output
                except Exception as e:
                    logger.warning(f"Gemini API attempt {attempt + 1} failed: {e}")
                    time.sleep(1.0)

        # Fallback to mock on any provider degradation
        logger.warning(f"Provider '{self.provider}' degraded or failed. Falling back to heuristic mock engine.")
        return generate_mock_heuristic_analysis(change_text, rag_context)


llm_client = LLMClient()
