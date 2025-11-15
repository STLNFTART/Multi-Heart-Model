/**
 * Regulatory Evidence Service
 *
 * This is the ONLY entry point for requesting regulatory evidence.
 * All simulation systems, LLMs, and reports go through this service.
 *
 * It orchestrates FDA, NHTSA, and FAA clients to produce a unified
 * RegulatoryEvidence package.
 */

import {
  RegulatoryEvidence,
  EvidenceRequest,
  RegulatoryQuery,
  RegulatoryFinding,
  EvidenceComparison,
  RegDomain,
} from '../types/RegulatoryEvidence';
import { FDAClient } from '../clients/FDAClient';
import { NHTSAClient } from '../clients/NHTSAClient';
import { FAAClient } from '../clients/FAAClient';

export class RegulatoryEvidenceService {
  private fdaClient: FDAClient;
  private nhtsaClient: NHTSAClient;
  private faaClient: FAAClient;

  private evidenceCache: Map<string, RegulatoryEvidence> = new Map();

  constructor(fdaApiKey?: string) {
    this.fdaClient = new FDAClient(fdaApiKey);
    this.nhtsaClient = new NHTSAClient();
    this.faaClient = new FAAClient();
  }

  /**
   * Get regulatory evidence for a simulation run
   *
   * This is the primary public API method.
   */
  async getEvidenceForRun(request: EvidenceRequest): Promise<RegulatoryEvidence> {
    const { runId, domain } = request;

    // Check cache first
    const cacheKey = this.getCacheKey(request);
    const cached = this.evidenceCache.get(cacheKey);
    if (cached) {
      console.log(`[RegulatoryEvidence] Cache hit for ${runId}`);
      return cached;
    }

    console.log(`[RegulatoryEvidence] Gathering evidence for ${runId} (domain: ${domain})`);

    // Route to domain-specific handler
    let evidence: RegulatoryEvidence;

    switch (domain) {
      case 'medical':
        evidence = await this.getmedicalEvidence(request);
        break;
      case 'av':
        evidence = await this.getAVEvidence(request);
        break;
      case 'uav':
        evidence = await this.getUAVEvidence(request);
        break;
      case 'space':
        evidence = await this.getSpaceEvidence(request);
        break;
      default:
        throw new Error(`Unsupported domain: ${domain}`);
    }

    // Cache result
    this.evidenceCache.set(cacheKey, evidence);

    return evidence;
  }

  /**
   * Get evidence for medical/HBCM domain
   */
  private async getmedicalEvidence(request: EvidenceRequest): Promise<RegulatoryEvidence> {
    const queries: RegulatoryQuery[] = [];
    const findings: RegulatoryFinding[] = [];

    if (request.medical) {
      // Query FDA device recalls
      const fdaQuery = await this.fdaClient.query({
        deviceType: request.medical.deviceType || 'neuromodulation',
        deviceClass: request.medical.deviceClass,
      });
      queries.push(fdaQuery);

      if (fdaQuery.success) {
        // This would contain the actual API response in production
        // For now, parse empty array (would parse fdaQuery.data in real impl)
        const fdaFindings = this.fdaClient.parseFindings({ results: [] });
        findings.push(...fdaFindings);
      }

      // Query FDA adverse events
      const adverseEvents = await this.fdaClient.queryAdverseEvents({
        deviceType: request.medical.deviceType,
      });
      findings.push(...adverseEvents);
    }

    return this.buildEvidencePackage(request, queries, findings);
  }

  /**
   * Get evidence for autonomous vehicle domain
   */
  private async getAVEvidence(request: EvidenceRequest): Promise<RegulatoryEvidence> {
    const queries: RegulatoryQuery[] = [];
    const findings: RegulatoryFinding[] = [];

    if (request.av) {
      // Query NHTSA vehicle recalls
      const nhtsaQuery = await this.nhtsaClient.query({
        make: request.av.make,
        model: request.av.model,
        year: request.av.year,
        vin: request.av.vin,
      });
      queries.push(nhtsaQuery);

      if (nhtsaQuery.success) {
        const nhtsaFindings = this.nhtsaClient.parseFindings({ Results: [] });
        findings.push(...nhtsaFindings);
      }

      // Query NHTSA complaints
      if (request.av.make && request.av.model && request.av.year) {
        const complaints = await this.nhtsaClient.queryComplaints({
          make: request.av.make,
          model: request.av.model,
          year: request.av.year,
        });
        findings.push(...complaints);
      }
    }

    return this.buildEvidencePackage(request, queries, findings);
  }

  /**
   * Get evidence for UAV/drone domain
   */
  private async getUAVEvidence(request: EvidenceRequest): Promise<RegulatoryEvidence> {
    const queries: RegulatoryQuery[] = [];
    const findings: RegulatoryFinding[] = [];

    if (request.uav) {
      // Query FAA UAS regulations
      const faaQuery = await this.faaClient.query({
        manufacturer: request.uav.manufacturer,
        model: request.uav.model,
        weight: request.uav.weight,
        operationType: request.uav.operationType,
      });
      queries.push(faaQuery);

      if (faaQuery.success) {
        const faaFindings = this.faaClient.parseFindings({ directives: [] });
        findings.push(...faaFindings);
      }

      // Query UAS-specific regulations
      const uasRegs = await this.faaClient.queryUASRegulations({
        manufacturer: request.uav.manufacturer,
        model: request.uav.model,
        weight: request.uav.weight,
        operationType: request.uav.operationType,
      });
      findings.push(...uasRegs);

      // Query incidents
      const incidents = await this.faaClient.queryIncidents({
        manufacturer: request.uav.manufacturer,
        model: request.uav.model,
      });
      findings.push(...incidents);
    }

    return this.buildEvidencePackage(request, queries, findings);
  }

  /**
   * Get evidence for space domain
   */
  private async getSpaceEvidence(request: EvidenceRequest): Promise<RegulatoryEvidence> {
    // Space domain would query FAA/AST (Office of Commercial Space Transportation)
    // For now, return minimal evidence
    return this.buildEvidencePackage(request, [], []);
  }

  /**
   * Compare evidence across multiple runs
   */
  async compareEvidence(runIds: string[]): Promise<EvidenceComparison> {
    // Implementation would:
    // 1. Fetch evidence for each run
    // 2. Compare findings
    // 3. Identify commonalities and differences

    // Placeholder
    return {
      runIds,
      domain: 'medical',
      timestamp: new Date().toISOString(),
      differences: [],
      commonFindings: [],
      uniqueToRuns: {},
    };
  }

  /**
   * Get metrics summary from all clients
   */
  getMetricsSummary() {
    return {
      fda: this.fdaClient.getMetricsSummary(),
      nhtsa: this.nhtsaClient.getMetricsSummary(),
      faa: this.faaClient.getMetricsSummary(),
    };
  }

  /**
   * Build complete evidence package
   */
  private buildEvidencePackage(
    request: EvidenceRequest,
    queries: RegulatoryQuery[],
    findings: RegulatoryFinding[]
  ): RegulatoryEvidence {
    const criticalCount = findings.filter(f => f.severity === 'critical').length;
    const warningCount = findings.filter(f => f.severity === 'warn').length;
    const infoCount = findings.filter(f => f.severity === 'info').length;

    const systemsCovered = Array.from(new Set(queries.map(q => q.system)));

    return {
      runId: request.runId,
      domain: request.domain,
      timestamp: new Date().toISOString(),

      context: {
        system: this.getSystemName(request),
        scenario: this.getScenarioName(request),
        region: this.getRegion(request),
        metadata: this.getMetadata(request),
      },

      queries,
      findings,

      summary: {
        totalFindings: findings.length,
        criticalCount,
        warningCount,
        infoCount,
        systemsCovered,
        hasBlockingIssues: criticalCount > 0,
      },
    };
  }

  private getSystemName(request: EvidenceRequest): string {
    switch (request.domain) {
      case 'medical':
        return 'HBCM v2.1';
      case 'av':
        return 'MotorHandPro QUANT';
      case 'uav':
        return 'UAV Simulator';
      case 'space':
        return 'Space Mission Sim';
      default:
        return 'Unknown';
    }
  }

  private getScenarioName(request: EvidenceRequest): string {
    if (request.av) {
      return `${request.av.year} ${request.av.make} ${request.av.model}`;
    }
    if (request.medical) {
      return request.medical.deviceType || 'Medical device';
    }
    if (request.uav) {
      return request.uav.model || 'UAV operation';
    }
    return 'Unknown scenario';
  }

  private getRegion(request: EvidenceRequest): string {
    return (
      request.medical?.region ||
      request.av?.region ||
      request.uav?.region ||
      request.space?.region ||
      'US'
    );
  }

  private getMetadata(request: EvidenceRequest): Record<string, unknown> {
    return {
      ...request.medical,
      ...request.av,
      ...request.uav,
      ...request.space,
    };
  }

  private getCacheKey(request: EvidenceRequest): string {
    return `${request.runId}-${request.domain}-${JSON.stringify(request)}`;
  }
}
