# FDA - U.S. Food and Drug Administration

**Last Reviewed:** 2025-01-15
**Data Source:** openFDA API
**Official Site:** https://open.fda.gov/

---

## Overview

The openFDA API provides access to FDA public datasets including device recalls, adverse events, and drug safety reports. This integration uses openFDA to query device-related regulatory information for medical simulations.

## API Endpoints Used

### Device Enforcement Reports (Recalls)
- **Endpoint:** `https://api.fda.gov/device/enforcement.json`
- **Purpose:** Query medical device recalls
- **Coverage:** Class I, II, and III recalls
- **Update Frequency:** Weekly
- **Historical Data:** 2012-present

### Medical Device Adverse Events (MAUDE)
- **Endpoint:** `https://api.fda.gov/device/event.json`
- **Purpose:** Query adverse event reports for medical devices
- **Coverage:** Manufacturer and user facility reports
- **Update Frequency:** Quarterly
- **Historical Data:** 1992-present

## Authentication

### Without API Key
- **Rate Limit:** 240 requests per minute, 1,000 per day
- **Suitable For:** Development, low-volume testing

### With API Key (Recommended for Production)
- **Rate Limit:** 240 requests per minute, 120,000 per day
- **Obtain Key:** https://open.fda.gov/apis/authentication/
- **Configuration:** Set `FDA_API_KEY` environment variable

## Terms of Service Summary

### Permitted Use
- ✅ Academic and research purposes
- ✅ Commercial products and services
- ✅ Data aggregation and analysis
- ✅ Integration into medical simulation platforms
- ✅ Caching results for reasonable durations

### Restrictions
- ❌ No warranty or guarantee of data accuracy
- ❌ Data must not be misrepresented as official FDA guidance
- ❌ No circumventing rate limits
- ❌ Attribution required when publicly displaying FDA data

### Compliance Requirements
- **Attribution:** When displaying FDA data publicly, attribute to "openFDA"
- **Disclaimer:** Include disclaimer that data is from FDA but not validated by FDA for this use
- **Updates:** Do not rely on stale data; refresh regularly
- **Liability:** User assumes all liability for data interpretation and use

## Data Quality & Limitations

### Accuracy
- Data comes directly from FDA official databases
- Reports submitted by manufacturers and healthcare facilities
- Not all adverse events are reported (voluntary reporting system)
- Recall data is authoritative and official

### Completeness
- Device recalls: Comprehensive for FDA-regulated devices in U.S.
- Adverse events: Underreporting is common (estimated 1-10% of events reported)
- International data: Limited to devices marketed in U.S.

### Timeliness
- Recall data: Near real-time (24-48 hour lag)
- Adverse events: 1-3 month lag from occurrence to public availability

## Search Query Syntax

### Basic Search
```
search=product_description:"pacemaker"
```

### Device Class Filter
```
search=classification:"Class III"+AND+product_description:"neuromodulation"
```

### Date Range
```
search=recall_initiation_date:[20240101+TO+20241231]
```

### Pagination
```
limit=10&skip=0
```

## Response Structure

### Enforcement Report
```json
{
  "product_description": "Implantable Cardioverter Defibrillator",
  "reason_for_recall": "Software issue may prevent...",
  "classification": "Class II",
  "recall_initiation_date": "2024-01-15",
  "termination_date": null,
  "status": "Ongoing",
  "res_event_number": "88888",
  "product_code": "LWI"
}
```

### Severity Mapping
- **Class I:** Life-threatening → Critical
- **Class II:** Serious adverse health consequences → Warning
- **Class III:** Minor adverse effects → Info

## Integration Checklist

- [x] API key obtained and configured
- [x] Rate limiting implemented (240 req/min)
- [x] Retry logic with exponential backoff
- [x] Timeout enforcement (10 seconds max)
- [x] Error handling for API unavailability
- [x] Caching to reduce redundant queries
- [x] Metrics/logging for observability
- [x] Attribution in public-facing reports
- [x] Disclaimer about data interpretation

## Testing

### Test Query
```bash
curl "https://api.fda.gov/device/enforcement.json?search=product_description:neuromodulation&limit=5"
```

### Expected Response
- Status: 200 OK
- Results: Array of enforcement reports
- Meta: Total count, disclaimer

## References

- **API Documentation:** https://open.fda.gov/apis/device/
- **Terms of Service:** https://open.fda.gov/apis/authentication/
- **Device Classification:** https://www.fda.gov/medical-devices/classify-your-medical-device/device-classification-panels
- **MAUDE Database:** https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfmaude/search.cfm

## Support & Issues

- **API Status:** https://open.fda.gov/api-status/
- **Email:** open@fda.hhs.gov
- **GitHub Issues:** https://github.com/FDA/openfda

---

**Next Review Date:** 2025-04-15 (Quarterly)
