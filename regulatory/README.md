# Regulatory Evidence Layer

**Production-Grade Integration for FDA/NHTSA/FAA Regulatory Data**

This module provides a unified, secure, and compliant interface to regulatory databases across medical, automotive, and aviation domains. It acts as the ONLY entry point for regulatory data across all simulation systems, LLMs, and reporting tools.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Simulation Systems                        │
│  HBCM │ MotorHandPro │ AV/Carla │ UAV Sim │ LaTeX Reports    │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│            Regulatory Evidence Service (TypeScript)           │
│  - Single Public API: /reg-evidence                          │
│  - RegulatoryEvidence contract only                          │
│  - Caching, rate limiting, observability                     │
└───────────────────────────┬──────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
    ┌────────┐         ┌────────┐        ┌────────┐
    │  FDA   │         │ NHTSA  │        │  FAA   │
    │ Client │         │ Client │        │ Client │
    └────────┘         └────────┘        └────────┘
         │                  │                  │
         ▼                  ▼                  ▼
    openFDA API      NHTSA VPIC API    FAA Data Sources
```

## Core Principles

### 1. **Hard Boundaries**
- ✅ ONE public entry point: `RegulatoryEvidenceService.getEvidenceForRun()`
- ✅ Internal clients (FDA, NHTSA, FAA) are NEVER exported
- ✅ LLMs and sim systems only see `RegulatoryEvidence` interface

### 2. **Secrets Isolation**
- ✅ API keys ONLY from environment variables
- ✅ No keys in .env.example (placeholders only)
- ✅ Key usage scoped per provider

### 3. **Timeouts and Backoff**
- ✅ Enforced request timeouts (10-20 seconds)
- ✅ Exponential backoff with max retries (3 attempts)
- ✅ Hard ceiling to prevent sim runs from hanging

### 4. **Provider-Specific ToS Compliance**
- ✅ FDA, NHTSA, FAA compliance docs in `docs/providers/`
- ✅ Rate limiting per provider specifications
- ✅ Attribution requirements documented

### 5. **Observability**
- ✅ Per-provider request counters
- ✅ Error/timeout counts
- ✅ Latency histograms
- ✅ No logging of PHI or sensitive query params

## Quick Start

### Installation

```bash
cd regulatory
npm install
```

### Environment Setup

```bash
# Copy example env
cp .env.example .env

# Edit .env
FDA_API_KEY=your_fda_api_key_here  # Get from https://open.fda.gov/apis/authentication/
REGULATORY_SERVICE_URL=http://localhost:3001
REGULATORY_SERVICE_TIMEOUT=30
```

### Run Regulatory Service

```bash
# Start the TypeScript service
npm run start

# Or in development with hot reload
npm run dev
```

### Test the Service

```bash
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

## Integration Examples

### 1. HBCM Web Control Panel (Python/FastAPI)

```python
from regulatory.integrations.hbcm.regulatory_api import create_regulatory_router

# Add to FastAPI app
app.include_router(create_regulatory_router(), prefix="/api/reg")

# After simulation completes
from regulatory.integrations.hbcm.regulatory_api import attach_regulatory_evidence_to_run

evidence = await attach_regulatory_evidence_to_run(
    run_id="hbcm_20250115_001",
    simulation_metadata={
        "device_type": "implantable_neuromodulation",
        "device_class": 3
    },
    db_session=db_session
)

# Add to LaTeX report
from regulatory.integrations.hbcm.regulatory_api import format_evidence_for_latex

latex_section = format_evidence_for_latex(evidence)
# Insert into report template
```

### 2. MotorHandPro / AV Carla (TypeScript)

```typescript
import { RegulatoryEvidenceService } from './regulatory/service/RegulatoryEvidenceService';

const regService = new RegulatoryEvidenceService(process.env.FDA_API_KEY);

// After AV simulation completes
const evidence = await regService.getEvidenceForRun({
  runId: 'av_city_scenario_42',
  domain: 'av',
  av: {
    make: 'Tesla',
    model: 'Model 3',
    year: 2024,
  },
});

// Store with simulation results
await db.simRuns.update(runId, {
  regulatoryEvidence: evidence,
});

// Include in PDF report
const reportData = {
  ...simResults,
  regulatory: evidence,
};
await generatePDFReport(reportData);
```

### 3. UAV/Drone Simulation

```typescript
const evidence = await regService.getEvidenceForRun({
  runId: 'uav_mission_007',
  domain: 'uav',
  uav: {
    manufacturer: 'DJI',
    model: 'Mavic 3',
    weight: 0.895, // kg
    operationType: 'commercial',
  },
});

// Check for blocking issues
if (evidence.summary.hasBlockingIssues) {
  console.error('CRITICAL: Regulatory issues detected!');
  evidence.findings
    .filter(f => f.severity === 'critical')
    .forEach(f => console.error(`- ${f.system.toUpperCase()}: ${f.summary}`));
}
```

## MCP Tools for LLMs

Safe, constrained tools that LLMs can use WITHOUT direct API access:

### Available Tools
- `reg.getEvidenceForRun(run_id, domain)` - Get complete evidence
- `reg.summarizeEvidence(run_id)` - Natural language summary
- `reg.compareEvidence(run_ids)` - Compare multiple runs
- `reg.getCriticalFindings(run_id)` - Critical issues only
- `reg.getMetrics()` - Service health metrics

### Forbidden Tools
- ❌ `reg.callFdaRaw()` - Direct API access NOT exposed
- ❌ `reg.queryArbitraryEndpoint()` - No arbitrary queries

### Run MCP Server

```bash
npm run mcp:serve
```

## Node-RED Automation

Import the flow template:

```bash
# Import flow into Node-RED
cat regulatory/node-red/evidence-automation-flow.json

# Configure:
# 1. Update webhook URL in your sim stack
# 2. Set PostgreSQL credentials
# 3. Configure email/Slack alerts
# 4. Point to Grafana/Prometheus
```

Flow triggers when simulations complete and automatically:
1. Calls regulatory evidence service
2. Stores evidence in database
3. Updates Grafana dashboards
4. Sends alerts for critical findings

## Provider Documentation

See `docs/providers/` for detailed compliance information:

- **[FDA.md](docs/providers/FDA.md)** - openFDA API, device recalls, adverse events
- **[NHTSA.md](docs/providers/NHTSA.md)** - Vehicle safety, recalls, VIN decode
- **[FAA.md](docs/providers/FAA.md)** - UAS regulations, airworthiness directives

## API Reference

### RegulatoryEvidence Interface

```typescript
interface RegulatoryEvidence {
  runId: string;
  domain: "medical" | "av" | "uav" | "space";
  timestamp: string;

  context: {
    system?: string;
    scenario?: string;
    region?: string;
  };

  queries: RegulatoryQuery[];   // What was asked
  findings: RegulatoryFinding[]; // What was found

  summary: {
    totalFindings: number;
    criticalCount: number;
    warningCount: number;
    infoCount: number;
    systemsCovered: RegulatorySystem[];
    hasBlockingIssues: boolean;
  };
}
```

### Finding Severity Levels

- **critical**: Life-threatening, crash risk, FDA Class I recall
- **warn**: Serious adverse consequences, FDA Class II recall
- **info**: Minor issues, informational notes, FDA Class III recall

## Testing

```bash
# Run unit tests
npm test

# Run integration tests (requires API keys)
npm run test:integration

# Test specific provider
npm run test:fda
npm run test:nhtsa
npm run test:faa
```

## Monitoring & Metrics

### Prometheus Metrics

The service exposes metrics at `/metrics`:

```
# HELP regulatory_requests_total Total requests per provider
# TYPE regulatory_requests_total counter
regulatory_requests_total{system="fda"} 127
regulatory_requests_total{system="nhtsa"} 43
regulatory_requests_total{system="faa"} 8

# HELP regulatory_request_duration_seconds Request latency
# TYPE regulatory_request_duration_seconds histogram
regulatory_request_duration_seconds_bucket{system="fda",le="1"} 100
regulatory_request_duration_seconds_bucket{system="fda",le="5"} 125
regulatory_request_duration_seconds_bucket{system="fda",le="+Inf"} 127
```

### Get Metrics Summary

```bash
curl http://localhost:3001/metrics

# Or via TypeScript
const metrics = regService.getMetricsSummary();
console.log(metrics);
// {
//   fda: { totalRequests: 127, successCount: 125, errorRate: 0.016 },
//   nhtsa: { ... },
//   faa: { ... }
// }
```

## Production Checklist

- [ ] FDA API key obtained and configured
- [ ] Rate limiting enforced (240 req/min for FDA)
- [ ] Request timeouts configured (10-20 seconds)
- [ ] Retry logic with exponential backoff implemented
- [ ] Error handling for API unavailability
- [ ] Caching enabled (1 hour default)
- [ ] Metrics exported to Prometheus/Grafana
- [ ] No logging of PHI or sensitive params
- [ ] Attribution in public-facing reports
- [ ] Disclaimer about unofficial nature
- [ ] Provider ToS reviewed (see docs/providers/)
- [ ] Backup strategy for API downtime
- [ ] Alert thresholds configured (critical findings)

## Troubleshooting

### FDA API Timeout
```
Error: Request timeout after 10000ms
```
**Solution:** FDA API can be slow. Increase timeout or check https://open.fda.gov/api-status/

### NHTSA VIN Not Found
```
Error: VIN decode failed
```
**Solution:** Validate VIN format, check if U.S. market vehicle

### FAA Missing Data
```
Warning: FAA integration using mock data
```
**Solution:** Production requires AD parser implementation (see docs/providers/FAA.md)

### Rate Limit Exceeded
```
Error: 429 Too Many Requests
```
**Solution:** Reduce request rate, use caching, get FDA API key for higher limits

## Development Roadmap

### Phase 1: Core Functionality (Complete)
- [x] FDA client (device recalls, adverse events)
- [x] NHTSA client (vehicle recalls, VIN decode)
- [x] FAA client (UAS regulations, static rules)
- [x] RegulatoryEvidence unified interface
- [x] HBCM Python integration
- [x] MCP tools for LLMs
- [x] Node-RED automation flow
- [x] Provider compliance docs

### Phase 2: Production Hardening (In Progress)
- [x] Timeout enforcement
- [x] Exponential backoff retry logic
- [x] Metrics/observability
- [ ] Comprehensive integration tests
- [ ] Load testing
- [ ] Backup API fallbacks

### Phase 3: Advanced Features (Planned)
- [ ] FAA AD parser (PDF/XML)
- [ ] Aircraft registration database
- [ ] LAANC airspace authorization API
- [ ] Multi-region support (EU/EASA)
- [ ] Real-time NOTAM integration
- [ ] Predictive analytics on findings

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Adding new regulatory providers
- Extending domain support
- Writing tests
- Documentation standards

## License

MIT License - See [LICENSE](../LICENSE)

## Support

- **Issues:** https://github.com/STLNFTART/Multi-Heart-Model/issues
- **Email:** regulatory@multi-heart-model.org
- **Docs:** https://docs.multi-heart-model.org/regulatory

---

**Status:** ✅ Production-Ready for HBCM, AV domains | ⚠️ UAV requires FAA AD parser
