/**
 * Core Regulatory Evidence Type System
 *
 * This is the ONLY interface that simulation systems, LLMs, and reporting
 * tools should ever see. Raw API responses from FDA/NHTSA/FAA are NEVER
 * exposed beyond the internal client layer.
 *
 * @module RegulatoryEvidence
 */

export type RegDomain = "av" | "uav" | "medical" | "space";

export type RegulatorySystem = "fda" | "nhtsa" | "faa" | "easa";

export type EvidenceSeverity = "info" | "warn" | "critical";

/**
 * Query record - what was asked of each regulatory system
 */
export interface RegulatoryQuery {
  system: RegulatorySystem;
  endpoint: string;
  params: Record<string, unknown>;
  timestamp: string;
  success: boolean;
  errorMessage?: string;
}

/**
 * Finding - summarized result from a regulatory query
 *
 * This is ALWAYS a human-readable summary, never raw JSON from APIs.
 */
export interface RegulatoryFinding {
  system: RegulatorySystem;
  category: string;          // e.g., "recall", "advisory", "certification_status"
  summary: string;            // Natural language summary (max 500 chars)
  severity: EvidenceSeverity;
  affectedProducts?: string[]; // Product names/models affected
  dateIssued?: string;        // ISO 8601 date
  dateExpires?: string;       // ISO 8601 date (if applicable)
  referenceUrls: string[];    // Official regulatory URLs
  regulatoryIds?: string[];   // e.g., FDA recall number, NHTSA campaign ID
}

/**
 * Complete regulatory evidence package for a single run/scenario
 *
 * This is what gets stored alongside simulation results and appears in reports.
 */
export interface RegulatoryEvidence {
  // Identity
  runId: string;
  domain: RegDomain;
  timestamp: string;  // ISO 8601

  // Context
  context: {
    system?: string;          // e.g., "HBCM v2.1", "MotorHandPro QUANT"
    scenario?: string;        // e.g., "av_city_01", "cardiac_stress_test"
    region?: string;          // e.g., "US", "EU"
    metadata?: Record<string, unknown>;
  };

  // What was queried
  queries: RegulatoryQuery[];

  // What was found
  findings: RegulatoryFinding[];

  // Rollup
  summary: {
    totalFindings: number;
    criticalCount: number;
    warningCount: number;
    infoCount: number;
    systemsCovered: RegulatorySystem[];
    hasBlockingIssues: boolean;  // Any critical findings
  };
}

/**
 * Evidence request - what callers provide to get evidence
 */
export interface EvidenceRequest {
  runId: string;
  domain: RegDomain;

  // Domain-specific context
  medical?: {
    deviceType?: string;      // e.g., "implantable_neuromodulation"
    deviceClass?: 1 | 2 | 3;  // FDA device class
    intendedUse?: string;
    region?: string;
  };

  av?: {
    make?: string;
    model?: string;
    year?: number;
    vin?: string;  // If available
    region?: string;
  };

  uav?: {
    manufacturer?: string;
    model?: string;
    weight?: number;          // kg
    operationType?: "recreational" | "commercial" | "experimental";
    region?: string;
  };

  space?: {
    mission?: string;
    launchVehicle?: string;
    payload?: string;
    region?: string;
  };
}

/**
 * Evidence comparison result
 */
export interface EvidenceComparison {
  runIds: string[];
  domain: RegDomain;
  timestamp: string;

  differences: {
    findingId: string;
    presentIn: string[];      // Run IDs where this finding appeared
    severity: EvidenceSeverity;
    summary: string;
  }[];

  commonFindings: RegulatoryFinding[];
  uniqueToRuns: Record<string, RegulatoryFinding[]>;
}
