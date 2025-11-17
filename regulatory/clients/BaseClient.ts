/**
 * Base Regulatory Client
 *
 * All provider-specific clients (FDA, NHTSA, FAA) extend this.
 * Enforces timeouts, retry logic, and observability.
 */

import { RegulatorySystem, RegulatoryQuery, RegulatoryFinding } from '../types/RegulatoryEvidence';

export interface ClientConfig {
  apiKey?: string;
  baseUrl: string;
  timeout: number;          // milliseconds
  maxRetries: number;
  retryBackoffMs: number;   // initial backoff, doubles each retry
}

export interface RequestMetrics {
  system: RegulatorySystem;
  endpoint: string;
  startTime: number;
  endTime: number;
  success: boolean;
  statusCode?: number;
  error?: string;
}

/**
 * Abstract base client with built-in resilience
 */
export abstract class BaseRegulatoryClient {
  protected config: ClientConfig;
  protected metrics: RequestMetrics[] = [];

  constructor(config: ClientConfig) {
    this.config = config;
  }

  abstract get systemName(): RegulatorySystem;

  /**
   * Execute request with timeout and retry logic
   */
  protected async executeRequest<T>(
    endpoint: string,
    params: Record<string, unknown>,
    fetchFn: () => Promise<T>
  ): Promise<{ success: boolean; data?: T; error?: string }> {
    const maxRetries = this.config.maxRetries;
    let lastError: string | undefined;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      const startTime = Date.now();

      try {
        // Apply timeout
        const timeoutPromise = new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error('Request timeout')), this.config.timeout)
        );

        const data = await Promise.race([fetchFn(), timeoutPromise]);

        // Record success metrics
        this.recordMetric({
          system: this.systemName,
          endpoint,
          startTime,
          endTime: Date.now(),
          success: true,
          statusCode: 200,
        });

        return { success: true, data };
      } catch (error) {
        lastError = error instanceof Error ? error.message : String(error);

        // Record failure metrics
        this.recordMetric({
          system: this.systemName,
          endpoint,
          startTime,
          endTime: Date.now(),
          success: false,
          error: lastError,
        });

        // If not last attempt, wait with exponential backoff
        if (attempt < maxRetries) {
          const backoff = this.config.retryBackoffMs * Math.pow(2, attempt);
          await new Promise(resolve => setTimeout(resolve, backoff));
        }
      }
    }

    return { success: false, error: lastError };
  }

  /**
   * Record metrics for observability
   */
  protected recordMetric(metric: RequestMetrics): void {
    this.metrics.push(metric);

    // Keep only last 1000 metrics to avoid memory leak
    if (this.metrics.length > 1000) {
      this.metrics.shift();
    }

    // Log to console in dev, should integrate with proper telemetry in prod
    if (process.env.NODE_ENV === 'development') {
      const duration = metric.endTime - metric.startTime;
      console.log(
        `[${this.systemName}] ${metric.endpoint}: ${metric.success ? 'SUCCESS' : 'FAILED'} (${duration}ms)`
      );
      if (!metric.success && metric.error) {
        console.error(`  Error: ${metric.error}`);
      }
    }
  }

  /**
   * Get metrics summary (for monitoring dashboards)
   */
  public getMetricsSummary(): {
    system: RegulatorySystem;
    totalRequests: number;
    successCount: number;
    failureCount: number;
    avgLatencyMs: number;
    errorRate: number;
  } {
    const total = this.metrics.length;
    const successes = this.metrics.filter(m => m.success).length;
    const failures = total - successes;
    const avgLatency =
      total > 0
        ? this.metrics.reduce((sum, m) => sum + (m.endTime - m.startTime), 0) / total
        : 0;

    return {
      system: this.systemName,
      totalRequests: total,
      successCount: successes,
      failureCount: failures,
      avgLatencyMs: Math.round(avgLatency),
      errorRate: total > 0 ? failures / total : 0,
    };
  }

  /**
   * Abstract method: query the regulatory system
   */
  abstract query(params: Record<string, unknown>): Promise<RegulatoryQuery>;

  /**
   * Abstract method: transform raw results into findings
   */
  abstract parseFindings(rawData: unknown): RegulatoryFinding[];
}
