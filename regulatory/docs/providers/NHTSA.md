# NHTSA - National Highway Traffic Safety Administration

**Last Reviewed:** 2025-01-15
**Data Source:** NHTSA Vehicle Safety APIs
**Official Site:** https://www.nhtsa.gov/

---

## Overview

NHTSA provides public APIs for vehicle safety data including recalls, complaints, defect investigations, and crash test ratings. This integration uses NHTSA APIs to query vehicle-related regulatory information for autonomous vehicle simulations.

## API Endpoints Used

### Vehicle Recalls
- **Endpoint:** `https://api.nhtsa.gov/SafetyRatings/GetRecalls`
- **Purpose:** Query safety recalls by make/model/year
- **Coverage:** All U.S. market vehicles
- **Update Frequency:** Real-time
- **Historical Data:** 1966-present

### VIN-Specific Recalls
- **Endpoint:** `https://api.nhtsa.gov/SafetyRatings/GetRecallByVIN/{vin}`
- **Purpose:** Get recalls for specific VIN
- **Coverage:** VIN-specific recall campaigns
- **Accuracy:** High (VIN decoding is official)

### Vehicle Complaints
- **Endpoint:** `https://api.nhtsa.gov/complaints/complaintsByVehicle`
- **Purpose:** Consumer complaints by vehicle
- **Coverage:** Owner-reported issues
- **Historical Data:** 1995-present

### VIN Decoder
- **Endpoint:** `https://api.nhtsa.gov/vehicles/DecodeVin/{vin}`
- **Purpose:** Decode VIN to vehicle specifications
- **Coverage:** All U.S. market vehicles

## Authentication

**No API Key Required**
- Public access without authentication
- Reasonable use expected
- No official rate limits published
- Conservative approach: ~10 requests/minute recommended

## Terms of Service Summary

### Permitted Use
- ✅ Research and analysis
- ✅ Commercial applications
- ✅ Safety analysis and simulation
- ✅ Integration into vehicle safety platforms
- ✅ Data aggregation

### Restrictions
- ❌ No automated bulk downloads
- ❌ Do not overwhelm servers (respect rate limits)
- ❌ Data must not be misrepresented as official NHTSA guidance
- ❌ No warranty of data completeness or accuracy

### Compliance Requirements
- **Attribution:** Credit NHTSA when publicly displaying recall data
- **Disclaimer:** Clearly state data source and limitations
- **Accuracy:** Do not alter or misrepresent recall information
- **Updates:** Refresh data regularly (recalls change frequently)

## Data Quality & Limitations

### Accuracy
- **Recall Data:** Authoritative and official (from NHTSA databases)
- **Complaints:** User-submitted, unverified
- **VIN Decode:** Official manufacturer data

### Completeness
- **Recalls:** Comprehensive for U.S. market vehicles
- **Complaints:** Voluntary reporting (underrepresents actual issues)
- **International:** U.S. market vehicles only
- **Gray Market:** Limited coverage for non-U.S. spec vehicles

### Timeliness
- **Recalls:** Near real-time (announced same day)
- **Complaints:** 1-2 week lag from submission
- **Investigations:** Updated as cases progress

## Search Query Patterns

### By Make/Model/Year
```
https://api.nhtsa.gov/SafetyRatings/GetRecalls?make=Tesla&model=Model%203&modelYear=2024&format=json
```

### By VIN
```
https://api.nhtsa.gov/SafetyRatings/GetRecallByVIN/5YJ3E1EA7KF000001?format=json
```

### Complaints
```
https://api.nhtsa.gov/complaints/complaintsByVehicle?make=Tesla&model=Model%203&modelYear=2024&format=json
```

## Response Structure

### Recall Response
```json
{
  "Results": [
    {
      "NHTSACampaignNumber": "24V123000",
      "Manufacturer": "Tesla, Inc.",
      "Subject": "Autopilot Software Issue",
      "Component": "ELECTRICAL SYSTEM",
      "Summary": "The software may not adequately detect...",
      "Consequence": "Increased risk of crash",
      "Remedy": "Software update via OTA",
      "ReportReceivedDate": "2024-01-15",
      "ModelYear": 2024,
      "Make": "TESLA",
      "Model": "Model 3"
    }
  ],
  "Count": 1,
  "Message": "Results returned successfully"
}
```

### Severity Assessment
**Based on `Consequence` field:**
- **Contains "crash", "fire", "injury", "death":** Critical
- **Contains "loss of control", "failure", "malfunction":** Warning
- **Other:** Info

## VIN Decoding

### Format
```
5YJ3E1EA7KF000001
```

### Decode Response
```json
{
  "Results": [
    {"Variable": "Make", "Value": "TESLA"},
    {"Variable": "Model", "Value": "Model 3"},
    {"Variable": "Model Year", "Value": "2024"},
    {"Variable": "Plant Country", "Value": "UNITED STATES"}
  ]
}
```

## Integration Checklist

- [x] Conservative rate limiting (10 req/min)
- [x] Retry logic with exponential backoff
- [x] Timeout enforcement (15 seconds for slow API)
- [x] Error handling for API unavailability
- [x] VIN validation before queries
- [x] Caching to reduce redundant queries
- [x] Metrics/logging for observability
- [x] Attribution in public-facing reports

## API Limitations & Workarounds

### Slow Response Times
- **Issue:** NHTSA APIs can be slow (5-10 seconds)
- **Mitigation:** Set 15-second timeout, cache aggressively

### No Batch Queries
- **Issue:** Must query one vehicle at a time
- **Mitigation:** Parallel requests with rate limiting

### Limited Error Messages
- **Issue:** API returns generic errors
- **Mitigation:** Log full responses for debugging

### JSON Format Required
- **Issue:** Default is XML
- **Mitigation:** Always append `?format=json`

## Testing

### Test Query (Recalls)
```bash
curl "https://api.nhtsa.gov/SafetyRatings/GetRecalls?make=Tesla&model=Model%203&modelYear=2024&format=json"
```

### Test Query (VIN Decode)
```bash
curl "https://api.nhtsa.gov/vehicles/DecodeVin/5YJ3E1EA7KF000001?format=json"
```

### Expected Response
- Status: 200 OK
- Results: Array of results
- Count: Total count
- Message: Status message

## Common Issues

### 1. VIN Not Found
- **Cause:** Invalid VIN or non-U.S. vehicle
- **Solution:** Validate VIN format, check if U.S. market

### 2. No Recalls Found
- **Cause:** Vehicle has no recalls (common)
- **Solution:** Return empty array, not error

### 3. API Timeout
- **Cause:** NHTSA servers slow or overloaded
- **Solution:** Retry with backoff, cache results

## References

- **API Documentation:** https://vpic.nhtsa.dot.gov/api/
- **Recall Information:** https://www.nhtsa.gov/recalls
- **Complaints Database:** https://www-odi.nhtsa.dot.gov/downloads/
- **Defect Investigations:** https://www.nhtsa.gov/defects

## Support & Issues

- **Help Desk:** (888) 327-4236
- **Email:** vpic@dot.gov
- **Office of Defects Investigation:** ODI.NHTSA@dot.gov

---

**Next Review Date:** 2025-04-15 (Quarterly)
