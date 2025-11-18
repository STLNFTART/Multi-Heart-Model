"""
HBCM Regulatory Evidence Integration - FastAPI Backend

This module bridges the HBCM Python simulation stack to the TypeScript
regulatory evidence service. It provides REST endpoints for the HBCM
web control panel to request regulatory context for simulation runs.

Integration Pattern:
    1. HBCM simulation completes
    2. Web panel calls POST /api/reg/context
    3. FastAPI → HTTP request to Node/TS regulatory service
    4. Store evidence alongside run in database
    5. Pass to LaTeX report generator

Usage:
    from regulatory_api import create_regulatory_router
    app.include_router(create_regulatory_router(), prefix="/api/reg")
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
import os


class RegulatoryContext(BaseModel):
    """Request to get regulatory context for an HBCM run"""

    run_id: str = Field(..., description="HBCM simulation run ID")
    domain: str = Field(default="medical", description="Regulatory domain")
    signal: str = Field(..., description="Signal type (e.g., 'heart_brain_coupling')")

    external_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context for regulatory lookup"
    )


class RegulatoryEvidence(BaseModel):
    """Complete regulatory evidence package"""

    run_id: str
    domain: str
    timestamp: str

    context: Dict[str, Any]
    queries: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]

    summary: Dict[str, Any]


class RegulatoryEvidenceSummary(BaseModel):
    """Condensed summary for quick display"""

    run_id: str
    total_findings: int
    critical_count: int
    warning_count: int
    info_count: int
    has_blocking_issues: bool
    systems_covered: List[str]


# Configuration
REGULATORY_SERVICE_URL = os.getenv(
    'REGULATORY_SERVICE_URL',
    'http://localhost:3001'  # Default Node/TS service port
)

REGULATORY_SERVICE_TIMEOUT = int(os.getenv(
    'REGULATORY_SERVICE_TIMEOUT',
    '30'  # 30 seconds
))


def create_regulatory_router() -> APIRouter:
    """Create FastAPI router for regulatory endpoints"""

    router = APIRouter(tags=["regulatory"])

    @router.post("/context", response_model=RegulatoryEvidence)
    async def get_regulatory_context(request: RegulatoryContext):
        """
        Get regulatory evidence for an HBCM simulation run.

        This endpoint:
        1. Calls the TypeScript regulatory service
        2. Returns structured evidence
        3. Should be called AFTER simulation completes

        The evidence is then:
        - Stored alongside the run in the database
        - Passed to LaTeX report generator
        - Displayed in web control panel
        """

        # Build evidence request for TS service
        evidence_request = {
            "runId": request.run_id,
            "domain": request.domain,
            "medical": {
                "deviceType": request.external_context.get("device_type", "neuromodulation")
                if request.external_context else "neuromodulation",
                "deviceClass": request.external_context.get("device_class", 3)
                if request.external_context else 3,
                "intendedUse": request.external_context.get("intended_use",
                                                            "cardiac neuromodulation")
                if request.external_context else "cardiac neuromodulation",
                "region": request.external_context.get("region", "US")
                if request.external_context else "US",
            }
        }

        try:
            async with httpx.AsyncClient(timeout=REGULATORY_SERVICE_TIMEOUT) as client:
                response = await client.post(
                    f"{REGULATORY_SERVICE_URL}/reg-evidence",
                    json=evidence_request
                )
                response.raise_for_status()

                evidence_data = response.json()
                return RegulatoryEvidence(**evidence_data)

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Regulatory service timeout - check FDA/NHTSA/FAA API status"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Regulatory service error: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch regulatory evidence: {str(e)}"
            )


    @router.get("/{run_id}/summary", response_model=RegulatoryEvidenceSummary)
    async def get_evidence_summary(run_id: str):
        """
        Get condensed summary of regulatory evidence for a run.

        Useful for quick dashboard display without fetching full evidence.
        """

        # In production, this would query your database
        # For now, fetch from regulatory service and condense

        try:
            async with httpx.AsyncClient(timeout=REGULATORY_SERVICE_TIMEOUT) as client:
                response = await client.get(
                    f"{REGULATORY_SERVICE_URL}/reg-evidence/{run_id}/summary"
                )
                response.raise_for_status()

                return RegulatoryEvidenceSummary(**response.json())

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"No regulatory evidence found for run {run_id}"
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Regulatory service error: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch evidence summary: {str(e)}"
            )


    @router.get("/metrics")
    async def get_regulatory_metrics():
        """
        Get metrics from regulatory service (request counts, latencies, etc.)

        Useful for monitoring dashboard to track FDA/NHTSA/FAA API health.
        """

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{REGULATORY_SERVICE_URL}/metrics"
                )
                response.raise_for_status()

                return response.json()

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch metrics: {str(e)}"
            )


    return router


# Example integration with HBCM simulation runner
async def attach_regulatory_evidence_to_run(
    run_id: str,
    simulation_metadata: Dict[str, Any],
    db_session  # Your database session
):
    """
    Attach regulatory evidence to a completed HBCM run.

    Call this AFTER simulation completes, BEFORE generating report.

    Args:
        run_id: HBCM simulation run ID
        simulation_metadata: Metadata from the simulation
        db_session: Database session to store evidence

    Example:
        >>> metadata = {
        ...     "device_type": "implantable_neuromodulation",
        ...     "device_class": 3,
        ...     "intended_use": "cardiac rhythm management"
        ... }
        >>> await attach_regulatory_evidence_to_run(
        ...     "hbcm_20250115_001",
        ...     metadata,
        ...     db_session
        ... )
    """

    evidence_request = RegulatoryContext(
        run_id=run_id,
        domain="medical",
        signal="heart_brain_coupling",
        external_context=simulation_metadata
    )

    async with httpx.AsyncClient(timeout=REGULATORY_SERVICE_TIMEOUT) as client:
        response = await client.post(
            f"{REGULATORY_SERVICE_URL}/reg-evidence",
            json=evidence_request.model_dump()
        )
        response.raise_for_status()

        evidence = response.json()

        # Store in database (pseudo-code - adjust for your ORM)
        # db_session.execute(
        #     insert(regulatory_evidence_table).values(
        #         run_id=run_id,
        #         evidence_json=evidence,
        #         timestamp=datetime.now()
        #     )
        # )
        # db_session.commit()

        return evidence


# LaTeX report integration
def format_evidence_for_latex(evidence: Dict[str, Any]) -> str:
    """
    Format regulatory evidence for inclusion in LaTeX reports.

    Returns LaTeX markup that can be inserted into HBCM reports.

    Args:
        evidence: RegulatoryEvidence dict

    Returns:
        LaTeX string for report inclusion
    """

    summary = evidence.get('summary', {})
    findings = evidence.get('findings', [])

    latex = r"""\section{Regulatory Evidence}

\subsection{Evidence Summary}

This simulation run was cross-referenced with regulatory databases on """ + \
        evidence.get('timestamp', 'unknown') + r""".

\begin{itemize}
    \item \textbf{Total Findings:} """ + str(summary.get('totalFindings', 0)) + r"""
    \item \textbf{Critical Issues:} """ + str(summary.get('criticalCount', 0)) + r"""
    \item \textbf{Warnings:} """ + str(summary.get('warningCount', 0)) + r"""
    \item \textbf{Informational:} """ + str(summary.get('infoCount', 0)) + r"""
    \item \textbf{Systems Checked:} """ + ', '.join(summary.get('systemsCovered', [])) + r"""
\end{itemize}

"""

    if summary.get('hasBlockingIssues'):
        latex += r"""\textbf{WARNING: Critical regulatory issues detected.}

"""

    if findings:
        latex += r"""\subsection{Findings}

\begin{itemize}
"""
        for finding in findings[:5]:  # Limit to top 5 for report brevity
            severity = finding.get('severity', 'info').upper()
            system = finding.get('system', 'unknown').upper()
            summary_text = finding.get('summary', 'No summary')

            latex += f"    \\item \\textbf{{{severity} ({system}):}} {summary_text}\n"

        if len(findings) > 5:
            latex += f"    \\item \\textit{{... and {len(findings) - 5} additional findings}}\n"

        latex += r"""\end{itemize}
"""

    latex += r"""
\textit{For full regulatory evidence, see appendix or contact regulatory affairs.}
"""

    return latex
