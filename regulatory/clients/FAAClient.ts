/**
 * FAA Client - Aviation Safety Database Integration
 *
 * Queries FAA databases for:
 * - Airworthiness Directives (ADs)
 * - Service Difficulty Reports (SDRs)
 * - UAS (drone) registrations and incidents
 * - Aircraft certifications
 *
 * API Docs: https://www.faa.gov/foia/electronic_reading_room
 * Note: FAA does not have a comprehensive public API like FDA/NHTSA
 * This client uses available datasets and may need scraping fallbacks
 *
 * Rate limits: No official API, use conservative delays
 */

import {
  RegulatorySystem,
  RegulatoryQuery,
  RegulatoryFinding,
  EvidenceSeverity,
} from '../types/RegulatoryEvidence';
import { BaseRegulatoryClient, ClientConfig } from './BaseClient';

interface FAAQueryParams {
  manufacturer?: string;
  model?: string;
  weight?: number;
  operationType?: 'recreational' | 'commercial' | 'experimental';
}

interface AirworthinessDirective {
  ad_number: string;
  subject: string;
  effective_date: string;
  affected_models: string[];
  compliance: string;
}

export class FAAClient extends BaseRegulatoryClient {
  // Note: FAA doesn't have a unified API, using data.gov datasets
  private static readonly BASE_URL = 'https://data.faa.gov/api';

  constructor() {
    super({
      baseUrl: FAAClient.BASE_URL,
      timeout: 20000, // 20 seconds (data.gov can be slow)
      maxRetries: 3,
      retryBackoffMs: 3000,
    });
  }

  get systemName(): RegulatorySystem {
    return 'faa';
  }

  /**
   * Query FAA databases
   *
   * Note: This is a simplified implementation. In production, you would:
   * 1. Query multiple FAA data sources
   * 2. Parse PDF/XML airworthiness directives
   * 3. Cross-reference with UAS incident reports
   * 4. Check drone registration requirements
   */
  async query(params: Record<string, unknown>): Promise<RegulatoryQuery> {
    const faaParams = params as FAAQueryParams;
    const timestamp = new Date().toISOString();

    // For now, we'll query a known FAA dataset on data.gov
    // In production, expand to multiple sources
    const endpoint = '/3/action/datastore_search';
    const resourceId = 'faa-airworthiness-directives'; // Example resource

    const url = `${this.config.baseUrl}${endpoint}?resource_id=${resourceId}&limit=10`;

    const result = await this.executeRequest(endpoint, params, async () => {
      // Note: This is a placeholder. Real implementation would:
      // - Parse XML/PDF ADs from rgl.faa.gov
      // - Query UAS incident database
      // - Check certification status

      // For demo, return mock data structure
      return this.getMockFAAData(faaParams);
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
   * Parse FAA results into standardized findings
   */
  parseFindings(rawData: unknown): RegulatoryFinding[] {
    const data = rawData as { directives?: AirworthinessDirective[] };

    if (!data.directives || data.directives.length === 0) {
      return [];
    }

    return data.directives.map(ad => {
      // Severity based on compliance urgency
      const severity = ad.compliance.toLowerCase().includes('immediate')
        ? 'critical'
        : ad.compliance.toLowerCase().includes('required')
        ? 'warn'
        : 'info';

      return {
        system: 'faa',
        category: 'airworthiness_directive',
        summary: `${ad.ad_number}: ${ad.subject.substring(0, 250)}`,
        severity: severity as EvidenceSeverity,
        affectedProducts: ad.affected_models,
        dateIssued: ad.effective_date,
        referenceUrls: [`https://rgl.faa.gov/Regulatory_and_Guidance_Library/rgAD.nsf/${ad.ad_number}`],
        regulatoryIds: [ad.ad_number],
      };
    });
  }

  /**
   * Query UAS (drone) specific regulations
   */
  async queryUASRegulations(params: FAAQueryParams): Promise<RegulatoryFinding[]> {
    const findings: RegulatoryFinding[] = [];

    // Weight-based classification
    if (params.weight) {
      if (params.weight > 25) {
        // > 25kg requires special certification
        findings.push({
          system: 'faa',
          category: 'uas_regulation',
          summary: 'Aircraft exceeds 25kg weight limit - requires Part 107 waiver and special airworthiness certification',
          severity: 'warn',
          affectedProducts: params.model ? [params.model] : [],
          dateIssued: '2024-01-01',
          referenceUrls: [
            'https://www.faa.gov/uas/commercial_operators/part_107_waivers',
          ],
          regulatoryIds: ['14 CFR 107.36'],
        });
      }

      if (params.weight > 0.25 && params.operationType !== 'recreational') {
        // Commercial operation > 250g
        findings.push({
          system: 'faa',
          category: 'uas_regulation',
          summary: 'Commercial UAS operation requires FAA Part 107 remote pilot certificate and aircraft registration',
          severity: 'info',
          affectedProducts: params.model ? [params.model] : [],
          dateIssued: '2016-08-29',
          referenceUrls: [
            'https://www.faa.gov/uas/commercial_operators',
          ],
          regulatoryIds: ['14 CFR Part 107'],
        });
      }
    }

    // Operation type restrictions
    if (params.operationType === 'commercial') {
      findings.push({
        system: 'faa',
        category: 'uas_regulation',
        summary: 'Commercial operations prohibited in certain airspace without FAA authorization (LAANC)',
        severity: 'info',
        affectedProducts: [],
        dateIssued: '2024-01-01',
        referenceUrls: [
          'https://www.faa.gov/uas/programs_partnerships/data_exchange',
        ],
        regulatoryIds: ['LAANC'],
      });
    }

    return findings;
  }

  /**
   * Check if aircraft/UAS is on incident list
   */
  async queryIncidents(params: FAAQueryParams): Promise<RegulatoryFinding[]> {
    // In production, query FAA accident/incident database
    // For now, return empty (no incidents found)
    return [];
  }

  /**
   * Mock FAA data for development/testing
   *
   * In production, replace with real API calls to:
   * - rgl.faa.gov (Regulatory & Guidance Library)
   * -Registry.faa.gov (Aircraft registration)
   * - data.faa.gov (Open data portal)
   */
  private getMockFAAData(params: FAAQueryParams): { directives: AirworthinessDirective[] } {
    // Example AD for demonstration
    const mockDirectives: AirworthinessDirective[] = [];

    if (params.manufacturer?.toLowerCase().includes('dji')) {
      mockDirectives.push({
        ad_number: '2024-UAS-001',
        subject: 'Battery thermal runaway risk in certain UAS models',
        effective_date: '2024-03-15',
        affected_models: ['DJI Mavic 3', 'DJI Air 3'],
        compliance: 'Required within 30 days - battery inspection and firmware update',
      });
    }

    return { directives: mockDirectives };
  }
}
