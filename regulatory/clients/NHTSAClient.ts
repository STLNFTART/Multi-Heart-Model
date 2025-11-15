/**
 * NHTSA Client - Vehicle Safety Database Integration
 *
 * Queries NHTSA databases for:
 * - Vehicle recalls (safety campaigns)
 * - Complaints
 * - Defect investigations
 * - Crash test ratings
 *
 * API Docs: https://vpic.nhtsa.dot.gov/api/
 * ToS: Public API, no key required, reasonable use expected
 *
 * Rate limits: Not explicitly stated, use reasonable delays
 */

import {
  RegulatorySystem,
  RegulatoryQuery,
  RegulatoryFinding,
  EvidenceSeverity,
} from '../types/RegulatoryEvidence';
import { BaseRegulatoryClient, ClientConfig } from './BaseClient';

interface NHTSARecall {
  NHTSACampaignNumber: string;
  Manufacturer: string;
  Subject: string;
  Component: string;
  Summary: string;
  Consequence: string;
  Remedy: string;
  ReportReceivedDate: string;
  ModelYear: number;
  Make: string;
  Model: string;
}

interface NHTSAQueryParams {
  make?: string;
  model?: string;
  year?: number;
  vin?: string;
}

export class NHTSAClient extends BaseRegulatoryClient {
  private static readonly BASE_URL = 'https://api.nhtsa.gov';

  constructor() {
    super({
      baseUrl: NHTSAClient.BASE_URL,
      timeout: 15000, // 15 seconds (NHTSA can be slow)
      maxRetries: 3,
      retryBackoffMs: 2000,
    });
  }

  get systemName(): RegulatorySystem {
    return 'nhtsa';
  }

  /**
   * Query NHTSA recalls database
   */
  async query(params: Record<string, unknown>): Promise<RegulatoryQuery> {
    const nhtsaParams = params as NHTSAQueryParams;
    const timestamp = new Date().toISOString();

    let endpoint: string;
    let url: string;

    if (nhtsaParams.vin) {
      // VIN-specific recall lookup
      endpoint = '/SafetyRatings/GetRecallByVIN';
      url = `${this.config.baseUrl}${endpoint}/${nhtsaParams.vin}?format=json`;
    } else if (nhtsaParams.make && nhtsaParams.model && nhtsaParams.year) {
      // Make/Model/Year recall lookup
      endpoint = '/SafetyRatings/GetRecalls';
      url = `${this.config.baseUrl}${endpoint}?make=${nhtsaParams.make}&model=${nhtsaParams.model}&modelYear=${nhtsaParams.year}&format=json`;
    } else {
      // Fallback: just search by make
      endpoint = '/SafetyRatings/GetRecalls';
      const make = nhtsaParams.make || 'Tesla'; // Default for demo
      url = `${this.config.baseUrl}${endpoint}?make=${make}&format=json`;
    }

    const result = await this.executeRequest(endpoint, params, async () => {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`NHTSA API error: ${response.status} ${response.statusText}`);
      }
      return response.json();
    });

    return {
      system: this.systemName,
      endpoint,
      params,
      timestamp,
      success: result.success,
      errorMessage: result.error,
    };
  }

  /**
   * Parse NHTSA recall results into standardized findings
   */
  parseFindings(rawData: unknown): RegulatoryFinding[] {
    const data = rawData as { Results?: NHTSARecall[] };

    if (!data.Results || data.Results.length === 0) {
      return [];
    }

    return data.Results.map(recall => {
      // Determine severity based on consequence text
      const severity = this.assessRecallSeverity(recall.Consequence);

      // Build reference URL
      const refUrl = `https://www.nhtsa.gov/recalls?nhtsaId=${recall.NHTSACampaignNumber}`;

      return {
        system: 'nhtsa',
        category: 'vehicle_recall',
        summary: `${recall.Component}: ${recall.Summary.substring(0, 250)}`,
        severity,
        affectedProducts: [`${recall.ModelYear} ${recall.Make} ${recall.Model}`],
        dateIssued: recall.ReportReceivedDate,
        referenceUrls: [refUrl],
        regulatoryIds: [recall.NHTSACampaignNumber],
      };
    });
  }

  /**
   * Query vehicle complaints
   */
  async queryComplaints(params: NHTSAQueryParams): Promise<RegulatoryFinding[]> {
    const endpoint = '/complaints/complaintsByVehicle';
    const make = params.make || 'Tesla';
    const model = params.model || 'Model 3';
    const year = params.year || 2024;

    const url = `${this.config.baseUrl}${endpoint}?make=${make}&model=${model}&modelYear=${year}&format=json`;

    const result = await this.executeRequest(endpoint, params, async () => {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`NHTSA API error: ${response.status}`);
      }
      return response.json();
    });

    if (!result.success || !result.data) {
      return [];
    }

    // Parse complaints (simplified)
    const complaints = (result.data as any).results || [];
    return complaints.slice(0, 5).map((complaint: any) => ({
      system: 'nhtsa' as const,
      category: 'vehicle_complaint',
      summary: complaint.summary?.substring(0, 300) || 'Complaint filed',
      severity: 'info' as EvidenceSeverity,
      affectedProducts: [`${year} ${make} ${model}`],
      dateIssued: complaint.dateComplaintFiled,
      referenceUrls: [],
      regulatoryIds: [complaint.odiNumber],
    }));
  }

  /**
   * Assess recall severity based on consequence description
   */
  private assessRecallSeverity(consequence: string): EvidenceSeverity {
    const lowerConsequence = consequence.toLowerCase();

    // Critical: crash, fire, injury, death
    if (
      lowerConsequence.includes('crash') ||
      lowerConsequence.includes('fire') ||
      lowerConsequence.includes('injury') ||
      lowerConsequence.includes('death')
    ) {
      return 'critical';
    }

    // Warn: loss of control, failure, malfunction
    if (
      lowerConsequence.includes('loss of') ||
      lowerConsequence.includes('fail') ||
      lowerConsequence.includes('malfunction')
    ) {
      return 'warn';
    }

    return 'info';
  }

  /**
   * Decode VIN to get vehicle details
   */
  async decodeVIN(vin: string): Promise<{
    make: string;
    model: string;
    year: number;
  } | null> {
    const endpoint = '/vehicles/DecodeVin';
    const url = `${this.config.baseUrl}${endpoint}/${vin}?format=json`;

    const result = await this.executeRequest(endpoint, { vin }, async () => {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`NHTSA VIN decode error: ${response.status}`);
      }
      return response.json();
    });

    if (!result.success || !result.data) {
      return null;
    }

    const results = (result.data as any).Results || [];
    const makeResult = results.find((r: any) => r.Variable === 'Make');
    const modelResult = results.find((r: any) => r.Variable === 'Model');
    const yearResult = results.find((r: any) => r.Variable === 'Model Year');

    if (!makeResult || !modelResult || !yearResult) {
      return null;
    }

    return {
      make: makeResult.Value,
      model: modelResult.Value,
      year: parseInt(yearResult.Value, 10),
    };
  }
}
