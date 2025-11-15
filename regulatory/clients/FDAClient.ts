/**
 * FDA Client - openFDA API Integration
 *
 * Queries FDA databases for:
 * - Device recalls (enforcement reports)
 * - Adverse events (MAUDE)
 * - Device classifications
 *
 * API Docs: https://open.fda.gov/apis/
 * ToS: https://open.fda.gov/apis/authentication/
 *
 * Rate limits:
 * - Without API key: 240 requests/minute, 1000/day
 * - With API key: 240 requests/minute, 120,000/day
 */

import {
  RegulatorySystem,
  RegulatoryQuery,
  RegulatoryFinding,
  EvidenceSeverity,
} from '../types/RegulatoryEvidence';
import { BaseRegulatoryClient, ClientConfig } from './BaseClient';

interface FDADeviceRecall {
  product_description: string;
  reason_for_recall: string;
  classification: string; // "Class I", "Class II", "Class III"
  recall_initiation_date: string;
  termination_date?: string;
  status: string;
  res_event_number: string;
  product_code?: string;
  k_number?: string;
  pma_number?: string;
}

interface FDAQueryParams {
  deviceType?: string;
  deviceClass?: 1 | 2 | 3;
  search?: string;
  limit?: number;
}

export class FDAClient extends BaseRegulatoryClient {
  private static readonly BASE_URL = 'https://api.fda.gov/device';

  constructor(apiKey?: string) {
    super({
      apiKey,
      baseUrl: FDAClient.BASE_URL,
      timeout: 10000, // 10 seconds
      maxRetries: 3,
      retryBackoffMs: 1000,
    });
  }

  get systemName(): RegulatorySystem {
    return 'fda';
  }

  /**
   * Query FDA device enforcement (recalls) database
   */
  async query(params: Record<string, unknown>): Promise<RegulatoryQuery> {
    const fdaParams = params as FDAQueryParams;
    const timestamp = new Date().toISOString();

    // Build FDA search query
    const searchTerms: string[] = [];

    if (fdaParams.deviceType) {
      searchTerms.push(`product_description:"${fdaParams.deviceType}"`);
    }

    if (fdaParams.deviceClass) {
      searchTerms.push(`classification:"Class ${fdaParams.deviceClass}"`);
    }

    if (fdaParams.search) {
      searchTerms.push(fdaParams.search);
    }

    const searchQuery = searchTerms.length > 0 ? searchTerms.join('+AND+') : '*';
    const limit = fdaParams.limit || 10;

    const endpoint = '/enforcement.json';
    const url = `${this.config.baseUrl}${endpoint}?search=${searchQuery}&limit=${limit}${
      this.config.apiKey ? `&api_key=${this.config.apiKey}` : ''
    }`;

    // Execute with retry/timeout logic
    const result = await this.executeRequest(endpoint, params, async () => {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`FDA API error: ${response.status} ${response.statusText}`);
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
   * Parse FDA enforcement results into standardized findings
   */
  parseFindings(rawData: unknown): RegulatoryFinding[] {
    const data = rawData as { results?: FDADeviceRecall[] };

    if (!data.results || data.results.length === 0) {
      return [];
    }

    return data.results.map(recall => {
      // Map FDA classification to severity
      const severity = this.mapClassificationToSeverity(recall.classification);

      // Build reference URL
      const refUrl = `https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfRES/res.cfm?id=${recall.res_event_number}`;

      return {
        system: 'fda',
        category: 'device_recall',
        summary: `${recall.classification}: ${recall.reason_for_recall.substring(0, 300)}`,
        severity,
        affectedProducts: [recall.product_description],
        dateIssued: recall.recall_initiation_date,
        dateExpires: recall.termination_date,
        referenceUrls: [refUrl],
        regulatoryIds: [recall.res_event_number],
      };
    });
  }

  /**
   * Query adverse events (MAUDE database)
   */
  async queryAdverseEvents(params: FDAQueryParams): Promise<RegulatoryFinding[]> {
    const endpoint = '/event.json';
    const searchQuery = params.deviceType
      ? `device.generic_name:"${params.deviceType}"`
      : '*';
    const limit = params.limit || 10;

    const url = `${this.config.baseUrl}${endpoint}?search=${searchQuery}&limit=${limit}${
      this.config.apiKey ? `&api_key=${this.config.apiKey}` : ''
    }`;

    const result = await this.executeRequest(endpoint, params, async () => {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`FDA API error: ${response.status}`);
      }
      return response.json();
    });

    if (!result.success || !result.data) {
      return [];
    }

    // Parse adverse events (simplified for now)
    const events = (result.data as any).results || [];
    return events.slice(0, 5).map((event: any) => ({
      system: 'fda' as const,
      category: 'adverse_event',
      summary: event.mdr_text?.[0]?.text?.substring(0, 300) || 'Adverse event reported',
      severity: 'warn' as EvidenceSeverity,
      affectedProducts: event.device?.map((d: any) => d.generic_name) || [],
      dateIssued: event.date_received,
      referenceUrls: [],
      regulatoryIds: [event.report_number],
    }));
  }

  /**
   * Map FDA recall classification to severity level
   */
  private mapClassificationToSeverity(classification: string): EvidenceSeverity {
    if (classification.includes('Class I')) {
      return 'critical'; // Dangerous or defective products that may cause serious injury or death
    } else if (classification.includes('Class II')) {
      return 'warn'; // Products that may cause temporary or medically reversible adverse health consequences
    } else {
      return 'info'; // Class III: Products not likely to cause adverse health consequences
    }
  }
}
