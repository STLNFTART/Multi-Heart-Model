# FAA - Federal Aviation Administration

**Last Reviewed:** 2025-01-15
**Data Source:** FAA Open Data, Airworthiness Directives, UAS Resources
**Official Site:** https://www.faa.gov/

---

## Overview

The FAA regulates civil aviation in the United States, including unmanned aircraft systems (UAS/drones). Unlike FDA and NHTSA, the FAA does not provide a comprehensive unified API. This integration uses multiple FAA data sources and may require web scraping fallbacks for complete coverage.

## Data Sources Used

### 1. Airworthiness Directives (ADs)
- **Source:** https://rgl.faa.gov/Regulatory_and_Guidance_Library/rgAD.nsf
- **Purpose:** Mandatory safety directives for aircraft
- **Format:** PDF/XML (no REST API)
- **Update Frequency:** Weekly
- **Coverage:** All U.S.-registered aircraft

### 2. UAS (Drone) Regulations
- **Source:** 14 CFR Part 107
- **Purpose:** Commercial drone operations rules
- **Access:** Static regulations, programmatically applied
- **Coverage:** All UAS operations in U.S. airspace

### 3. Aircraft Registration
- **Source:** https://registry.faa.gov/
- **Purpose:** Aircraft ownership and airworthiness status
- **Format:** Releasable Database (monthly downloads)
- **Access:** Bulk download, not real-time API

### 4. Service Difficulty Reports (SDRs)
- **Source:** https://av-info.faa.gov/
- **Purpose:** Reported aircraft malfunctions
- **Format:** Web portal (limited API access)
- **Coverage:** Commercial and general aviation

### 5. UAS Incident Reports
- **Source:** https://www.faa.gov/uas/resources/public_records/uas_sightings_report/
- **Purpose:** UAS safety events and near-misses
- **Format:** Quarterly PDF reports
- **Access:** Manual download/parsing

## API Status

### Available APIs
- ❌ No unified FAA API
- ⚠️ Limited data.gov datasets
- ⚠️ NOTAM API (flight restrictions, not device safety)

### Current Implementation
Our integration currently:
1. Uses static rule application for UAS regulations (14 CFR 107)
2. Implements mock data structures for ADs (placeholder)
3. **Production deployment requires:**
   - PDF/XML parsing for Airworthiness Directives
   - Bulk data downloads for registration database
   - Web scraping for incident reports

## Authentication

**No Authentication Required**
- Public data access
- No API keys
- Rate limits: N/A (static data or manual downloads)

## Terms of Service Summary

### Permitted Use
- ✅ Research and analysis
- ✅ Safety applications
- ✅ Commercial aviation software
- ✅ UAS compliance checking
- ✅ Educational purposes

### Restrictions
- ❌ Data must not be misrepresented as official FAA guidance
- ❌ No bulk automated scraping of websites
- ❌ Do not interfere with FAA website operations
- ❌ No warranty of data completeness

### Compliance Requirements
- **Attribution:** Credit FAA for all regulatory data
- **Disclaimer:** Clearly state unofficial nature of integration
- **Updates:** Do not rely on stale regulatory data
- **Responsibility:** Users responsible for verifying compliance

## UAS Regulatory Rules (14 CFR Part 107)

### Weight-Based Requirements

#### < 250 grams
- **Registration:** Not required (recreational)
- **Pilot Certificate:** Not required (recreational)
- **Commercial:** Requires Part 107 if commercial use

#### 250g - 25kg (0.25 - 25 kg)
- **Registration:** Required
- **Pilot Certificate:** Part 107 remote pilot certificate (commercial)
- **Recreational:** TRUST certificate (free online test)

#### > 25 kg
- **Certification:** Special airworthiness certificate required
- **Waiver:** Part 107 waiver for weight limit
- **Operation:** Highly restricted

### Operational Restrictions
- **Altitude:** < 400 feet AGL
- **Visibility:** Visual line of sight (VLOS)
- **Airspace:** Class G uncontrolled airspace (or LAANC authorization)
- **Night:** Requires anti-collision lighting
- **People:** Not over people without waiver

## Programmatic Compliance Checks

### Weight Check
```typescript
if (weight_kg > 25) {
  return {
    severity: 'warn',
    message: 'Exceeds 25kg - requires special airworthiness certification',
    reference: '14 CFR 107.36'
  };
}
```

### Operation Type Check
```typescript
if (operationType === 'commercial' && weight_kg > 0.25) {
  return {
    severity: 'info',
    message: 'Commercial operation requires Part 107 remote pilot certificate',
    reference: '14 CFR Part 107'
  };
}
```

### Airspace Check
```typescript
// Would integrate with LAANC API (if using B-UASFM)
// https://www.faa.gov/uas/programs_partnerships/data_exchange
```

## Airworthiness Directives

### Structure
```xml
<AD_NUMBER>2024-01-01</AD_NUMBER>
<SUBJECT>Battery thermal runaway in DJI Mavic 3</SUBJECT>
<EFFECTIVE_DATE>2024-03-15</EFFECTIVE_DATE>
<COMPLIANCE>Within 30 days - battery inspection</COMPLIANCE>
<AFFECTED_MODELS>
  <MODEL>DJI Mavic 3</MODEL>
  <MODEL>DJI Air 3</MODEL>
</AFFECTED_MODELS>
```

### Severity Determination
- **Immediate compliance:** Critical
- **Required compliance:** Warning
- **Optional/recommended:** Info

## Integration Checklist

### Current Status
- [x] UAS rule application (static logic)
- [x] Weight-based compliance checks
- [x] Operation type validation
- [ ] ⚠️ Airworthiness Directive parsing (TODO)
- [ ] ⚠️ Aircraft registration lookups (TODO)
- [ ] ⚠️ Incident report integration (TODO)
- [x] Mock data for development
- [x] Error handling
- [x] Attribution in reports

### Production Requirements
- [ ] PDF parser for ADs (https://rgl.faa.gov)
- [ ] Bulk database download automation
- [ ] Web scraper for incident reports
- [ ] LAANC API integration (optional)

## Data Quality & Limitations

### Accuracy
- **UAS Rules:** Authoritative (direct from 14 CFR)
- **Airworthiness Directives:** Official when sourced from rgl.faa.gov
- **Incidents:** Voluntary reporting (incomplete)

### Completeness
- **UAS Regulations:** Complete for U.S. operations
- **Aircraft Data:** Comprehensive for U.S.-registered aircraft
- **International:** Limited to U.S. jurisdiction

### Timeliness
- **Regulations:** Updated as published in Federal Register
- **ADs:** Published weekly
- **Incident Reports:** Quarterly lag

## Testing

### Test UAS Compliance (Mock)
```typescript
const params = {
  manufacturer: 'DJI',
  model: 'Mavic 3',
  weight: 0.895,  // kg
  operationType: 'commercial'
};

const findings = await faaClient.queryUASRegulations(params);
// Returns:
// - Part 107 certificate requirement
// - Registration requirement
// - LAANC airspace authorization note
```

## Workarounds for Missing API

### 1. Static Rule Engine
- Implement FAA regulations as code
- Apply rules based on vehicle parameters
- Update rules when regulations change

### 2. Scheduled Data Pulls
- Download bulk datasets monthly
- Parse PDF ADs weekly
- Update local database

### 3. Manual Curation
- Maintain curated list of high-impact ADs
- Focus on common UAS models
- Supplement with manual research

## References

- **Part 107 Regulations:** https://www.ecfr.gov/current/title-14/chapter-I/subchapter-F/part-107
- **Airworthiness Directives:** https://rgl.faa.gov/Regulatory_and_Guidance_Library/rgAD.nsf
- **UAS Resources:** https://www.faa.gov/uas
- **LAANC (Airspace Authorization):** https://www.faa.gov/uas/programs_partnerships/data_exchange
- **Aircraft Registration:** https://registry.faa.gov/

## Support & Issues

- **UAS Support:** (844) FLY-MY-UA / (844) 359-6982
- **General Info:** (866) TELL-FAA / (866) 835-5322
- **Email:** uas@faa.gov

## Future Enhancements

### Priority 1 (Production-Critical)
1. AD parser for real-time safety directives
2. Aircraft registration database integration

### Priority 2 (Nice-to-Have)
1. LAANC API for airspace authorization checks
2. Automated incident report parsing
3. eLogbook integration for maintenance tracking

### Priority 3 (Advanced)
1. Real-time NOTAM integration
2. Weather briefing API (aviationweather.gov)
3. Airport/airspace database (NASR)

---

**Next Review Date:** 2025-04-15 (Quarterly)
**Production Status:** ⚠️ MOCK DATA - Requires AD parser for full functionality
