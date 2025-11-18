# Regulatory Evidence Layer - Complete Integration Guide

This guide shows how to wire ONE pipeline end-to-end with regulatory evidence. We'll start with **HBCM** as the reference implementation.

---

## Prerequisites

1. **HBCM Web Control Panel** running (FastAPI backend)
2. **PostgreSQL database** for storing evidence
3. **LaTeX report generator** for HBCM
4. **Node.js 18+** for TypeScript regulatory service
5. **FDA API key** (optional but recommended)

---

## Step 1: Deploy Regulatory Service

### 1.1 Install Dependencies

```bash
cd regulatory
npm install
```

### 1.2 Configure Environment

```bash
cp .env.example .env

# Edit .env
FDA_API_KEY=your_actual_api_key  # Get from https://open.fda.gov/apis/authentication/
PORT=3001
DATABASE_URL=postgresql://user:pass@localhost:5432/hbcm_production
```

### 1.3 Build and Start Service

```bash
# Build TypeScript
npm run build

# Start service
npm start

# Or for development with hot reload
npm run dev
```

### 1.4 Verify Service is Running

```bash
curl http://localhost:3001/health
# Expected: {"status": "ok", "service": "regulatory-evidence"}

# Test FDA query
curl -X POST http://localhost:3001/reg-evidence \
  -H "Content-Type: application/json" \
  -d '{
    "runId": "test_001",
    "domain": "medical",
    "medical": {
      "deviceType": "neuromodulation",
      "deviceClass": 3
    }
  }'
```

---

## Step 2: Integrate with HBCM Backend (Python/FastAPI)

### 2.1 Install Python Dependencies

```bash
# In your HBCM backend directory
pip install httpx  # For async HTTP requests
```

### 2.2 Add Regulatory Router to FastAPI App

```python
# main.py or app.py
from fastapi import FastAPI
from regulatory.integrations.hbcm.regulatory_api import create_regulatory_router

app = FastAPI()

# Add regulatory endpoints
app.include_router(create_regulatory_router(), prefix="/api/reg", tags=["regulatory"])

# Your existing HBCM endpoints
@app.post("/api/simulations/run")
async def run_simulation(config: SimulationConfig):
    # Run HBCM simulation
    results = await hbcm_simulator.run(config)

    # IMPORTANT: After simulation completes, fetch regulatory evidence
    from regulatory.integrations.hbcm.regulatory_api import attach_regulatory_evidence_to_run

    evidence = await attach_regulatory_evidence_to_run(
        run_id=results.run_id,
        simulation_metadata={
            "device_type": config.device_type or "implantable_neuromodulation",
            "device_class": 3,
            "intended_use": config.intended_use or "cardiac neuromodulation",
            "region": "US"
        },
        db_session=db_session
    )

    # Store evidence with results
    results.regulatory_evidence = evidence

    return results
```

### 2.3 Update Database Schema

```sql
-- Add regulatory evidence table
CREATE TABLE regulatory_evidence (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(255) NOT NULL UNIQUE,
    domain VARCHAR(50) NOT NULL,
    evidence_json JSONB NOT NULL,
    critical_count INTEGER DEFAULT 0,
    warning_count INTEGER DEFAULT 0,
    info_count INTEGER DEFAULT 0,
    has_blocking_issues BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT fk_run_id FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id)
);

-- Index for fast lookups
CREATE INDEX idx_reg_evidence_run_id ON regulatory_evidence(run_id);
CREATE INDEX idx_reg_evidence_critical ON regulatory_evidence(has_blocking_issues) WHERE has_blocking_issues = TRUE;
```

---

## Step 3: Update LaTeX Report Generator

### 3.1 Modify Report Template

```latex
% hbcm_report_template.tex

\documentclass{article}
\usepackage{hyperref}
\usepackage{graphicx}

\begin{document}

\title{HBCM Simulation Report}
\author{Multi-Heart-Model System}
\date{\VAR{timestamp}}
\maketitle

% ... existing sections ...

% NEW SECTION: Regulatory Evidence
\BLOCK{if regulatory_evidence}
\VAR{regulatory_evidence_latex}
\BLOCK{endif}

% ... rest of report ...

\end{document}
```

### 3.2 Update Report Generator Code

```python
# report_generator.py
from jinja2 import Environment, FileSystemLoader
from regulatory.integrations.hbcm.regulatory_api import format_evidence_for_latex

def generate_hbcm_report(run_id: str, simulation_results: dict, evidence: dict):
    """Generate PDF report with regulatory evidence."""

    # Format regulatory evidence for LaTeX
    regulatory_latex = format_evidence_for_latex(evidence)

    # Prepare template variables
    context = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "simulation_results": simulation_results,
        "regulatory_evidence": evidence,
        "regulatory_evidence_latex": regulatory_latex,  # LaTeX-formatted section
    }

    # Render LaTeX template
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('hbcm_report_template.tex')
    latex_content = template.render(context)

    # Compile to PDF
    pdf_path = compile_latex_to_pdf(latex_content, run_id)

    return pdf_path
```

---

## Step 4: Update HBCM Web Dashboard

### 4.1 Add Regulatory Evidence Display

```javascript
// Dashboard.jsx or Dashboard.tsx
import React, { useEffect, useState } from 'react';

function RegulatoryEvidencePanel({ runId }) {
  const [evidence, setEvidence] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch evidence summary
    fetch(`/api/reg/${runId}/summary`)
      .then(res => res.json())
      .then(data => {
        setEvidence(data);
        setLoading(false);
      });
  }, [runId]);

  if (loading) return <div>Loading regulatory evidence...</div>;
  if (!evidence) return <div>No regulatory data available</div>;

  return (
    <div className="regulatory-evidence-panel">
      <h3>Regulatory Evidence Summary</h3>

      {evidence.has_blocking_issues && (
        <div className="alert alert-critical">
          ⚠️ CRITICAL: {evidence.critical_count} blocking regulatory issues detected
        </div>
      )}

      <div className="evidence-stats">
        <div className="stat">
          <span className="label">Total Findings:</span>
          <span className="value">{evidence.total_findings}</span>
        </div>
        <div className="stat">
          <span className="label">Critical:</span>
          <span className="value critical">{evidence.critical_count}</span>
        </div>
        <div className="stat">
          <span className="label">Warnings:</span>
          <span className="value warning">{evidence.warning_count}</span>
        </div>
        <div className="stat">
          <span className="label">Info:</span>
          <span className="value info">{evidence.info_count}</span>
        </div>
      </div>

      <div className="systems-checked">
        <strong>Systems Checked:</strong> {evidence.systems_covered.join(', ').toUpperCase()}
      </div>

      <button onClick={() => window.open(`/api/reg/${runId}/full`, '_blank')}>
        View Full Evidence Report
      </button>
    </div>
  );
}
```

---

## Step 5: Set Up Node-RED Automation (Optional)

### 5.1 Import Flow

1. Open Node-RED UI (usually http://localhost:1880)
2. Menu → Import
3. Paste contents of `regulatory/node-red/evidence-automation-flow.json`
4. Click "Import"

### 5.2 Configure Flow Nodes

1. **PostgreSQL Node:**
   - Update credentials
   - Set database to your HBCM production DB

2. **Email Alert Node:**
   - Set SMTP server
   - Configure recipient email

3. **Slack Alert Node:**
   - Update webhook URL to your Slack workspace

4. **Prometheus Push Node:**
   - Point to your Pushgateway instance

### 5.3 Wire to HBCM

```python
# After simulation completes, trigger Node-RED webhook
import httpx

async def trigger_regulatory_automation(run_id: str, domain: str, metadata: dict):
    """Trigger Node-RED evidence automation flow."""
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://node-red:1880/webhook/sim-complete",
            json={
                "run_id": run_id,
                "domain": domain,
                "metadata": metadata
            }
        )
```

---

## Step 6: Enable MCP Tools for LLMs

### 6.1 Start MCP Server

```bash
cd regulatory
npm run mcp:serve
```

### 6.2 Configure Claude Desktop (or other MCP client)

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "regulatory-evidence": {
      "command": "node",
      "args": ["/path/to/Multi-Heart-Model/regulatory/dist/mcp/server.js"]
    }
  }
}
```

### 6.3 Use in Claude Prompts

```
User: "Check the regulatory evidence for HBCM run hbcm_20250115_001"

Claude: [calls reg.getEvidenceForRun("hbcm_20250115_001", "medical")]

Claude: "I found 3 regulatory findings for run hbcm_20250115_001:
- 0 critical issues ✓
- 1 warning: FDA Class II recall for similar neuromodulation devices
- 2 informational notes about device classification

No blocking issues detected. The simulation can proceed."
```

---

## Step 7: Monitoring and Alerting

### 7.1 Add Prometheus Scrape Config

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'regulatory-evidence'
    static_configs:
      - targets: ['localhost:3001']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### 7.2 Create Grafana Dashboard

Import dashboard JSON:

```json
{
  "dashboard": {
    "title": "Regulatory Evidence Metrics",
    "panels": [
      {
        "title": "Request Rate by Provider",
        "targets": [
          {
            "expr": "rate(regulatory_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "regulatory_requests_total{status='error'} / regulatory_requests_total"
          }
        ]
      },
      {
        "title": "Critical Findings",
        "targets": [
          {
            "expr": "sum(regulatory_findings{severity='critical'})"
          }
        ]
      }
    ]
  }
}
```

### 7.3 Set Up Alerts

```yaml
# alerting_rules.yml
groups:
  - name: regulatory_evidence
    rules:
      - alert: RegulatoryServiceDown
        expr: up{job="regulatory-evidence"} == 0
        for: 5m
        annotations:
          summary: "Regulatory evidence service is down"

      - alert: CriticalFindingsDetected
        expr: sum(regulatory_findings{severity="critical"}) > 0
        annotations:
          summary: "Critical regulatory issues found"

      - alert: HighErrorRate
        expr: rate(regulatory_requests_total{status="error"}[5m]) > 0.1
        for: 10m
        annotations:
          summary: "Regulatory evidence service high error rate"
```

---

## Step 8: End-to-End Test

### 8.1 Run Complete Workflow

```bash
# 1. Start regulatory service
cd regulatory
npm start &

# 2. Start HBCM backend
cd ../hbcm_backend
uvicorn main:app --reload &

# 3. Run simulation via API
curl -X POST http://localhost:8000/api/simulations/run \
  -H "Content-Type: application/json" \
  -d '{
    "device_type": "implantable_neuromodulation",
    "device_class": 3,
    "simulation_config": {
      "duration": 120.0,
      "timestep": 0.001
    }
  }'

# 4. Check regulatory evidence was attached
curl http://localhost:8000/api/reg/{run_id}/summary

# 5. Download PDF report with evidence
curl http://localhost:8000/api/reports/{run_id}/pdf -o report.pdf
```

### 8.2 Verify Each Component

✅ **Regulatory Service:**
```bash
curl http://localhost:3001/metrics
# Should show request counts
```

✅ **Database:**
```sql
SELECT run_id, critical_count, has_blocking_issues FROM regulatory_evidence LIMIT 5;
```

✅ **Node-RED:**
- Check flow execution history
- Verify evidence stored in DB
- Check Grafana for new metrics

✅ **PDF Report:**
- Open report.pdf
- Verify "Regulatory Evidence" section exists
- Check findings are properly formatted

---

## Troubleshooting

### Service Won't Start
```
Error: Cannot find module '@modelcontextprotocol/sdk'
```
**Solution:** `cd regulatory && npm install`

### API Timeout
```
Error: Request timeout after 10000ms
```
**Solution:** Increase timeout in `.env`: `TIMEOUT_FDA=20000`

### No Findings Returned
```
{"findings": [], "summary": {"totalFindings": 0}}
```
**Solution:** Normal if no recalls match criteria. Try broader query or check FDA API status.

### Database Connection Failed
```
Error: ECONNREFUSED 127.0.0.1:5432
```
**Solution:** Verify PostgreSQL is running and DATABASE_URL is correct

---

## Next Steps

Once HBCM is working end-to-end:

1. **Clone pattern to MotorHandPro:**
   - Create `regulatory/integrations/motorhand/`
   - Follow same structure as HBCM integration
   - Use NHTSA client instead of FDA

2. **Clone pattern to AV/Carla:**
   - Create `regulatory/integrations/av/`
   - Integrate with Carla scenario completion hooks
   - Store evidence with sim results

3. **Add more providers:**
   - EASA (European aviation)
   - Transport Canada
   - MHRA (UK medicines)

---

## Production Deployment Checklist

- [ ] All API keys in secret manager (not .env files)
- [ ] Rate limiting enforced per provider
- [ ] Monitoring and alerting configured
- [ ] Database backups enabled
- [ ] Load balancer for regulatory service (if high volume)
- [ ] CDN for static assets/reports
- [ ] Compliance review completed
- [ ] User training on regulatory findings
- [ ] Disaster recovery plan documented

---

**Status:** This guide successfully integrates regulatory evidence into HBCM. Repeat for other pipelines.
