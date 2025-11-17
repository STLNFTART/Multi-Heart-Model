/**
 * MCP Server for Regulatory Evidence
 *
 * Implements the constrained MCP tools defined in regulatory_tools.json.
 * This server ensures LLMs NEVER get direct access to raw FDA/NHTSA/FAA APIs.
 *
 * All tools return structured, sanitized RegulatoryEvidence data.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

import { RegulatoryEvidenceService } from '../service/RegulatoryEvidenceService.js';
import {
  RegulatoryEvidence,
  EvidenceRequest,
  RegDomain,
} from '../types/RegulatoryEvidence.js';

const FDA_API_KEY = process.env.FDA_API_KEY;

const regulatoryService = new RegulatoryEvidenceService(FDA_API_KEY);

const server = new Server(
  {
    name: 'regulatory-evidence-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

/**
 * List available tools
 */
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'reg.getEvidenceForRun',
        description:
          'Get complete regulatory evidence package for a simulation run. Returns structured evidence from FDA/NHTSA/FAA databases.',
        inputSchema: {
          type: 'object',
          properties: {
            run_id: {
              type: 'string',
              description: "Simulation run ID (e.g., 'hbcm_20250115_001')",
            },
            domain: {
              type: 'string',
              enum: ['medical', 'av', 'uav', 'space'],
              description: 'Regulatory domain for the simulation',
            },
          },
          required: ['run_id', 'domain'],
        },
      },
      {
        name: 'reg.summarizeEvidence',
        description:
          'Get a concise natural-language summary of regulatory evidence for a run.',
        inputSchema: {
          type: 'object',
          properties: {
            run_id: {
              type: 'string',
              description: 'Simulation run ID',
            },
          },
          required: ['run_id'],
        },
      },
      {
        name: 'reg.compareEvidence',
        description:
          'Compare regulatory evidence across multiple simulation runs.',
        inputSchema: {
          type: 'object',
          properties: {
            run_ids: {
              type: 'array',
              items: { type: 'string' },
              minItems: 2,
              maxItems: 5,
              description: 'List of run IDs to compare (2-5 runs)',
            },
          },
          required: ['run_ids'],
        },
      },
      {
        name: 'reg.getCriticalFindings',
        description:
          'Get ONLY critical severity findings for a run. Use this to quickly check for blocking regulatory issues.',
        inputSchema: {
          type: 'object',
          properties: {
            run_id: {
              type: 'string',
              description: 'Simulation run ID',
            },
          },
          required: ['run_id'],
        },
      },
      {
        name: 'reg.getMetrics',
        description:
          'Get health metrics for regulatory data sources (FDA/NHTSA/FAA).',
        inputSchema: {
          type: 'object',
          properties: {},
          required: [],
        },
      },
    ],
  };
});

/**
 * Handle tool calls
 */
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'reg.getEvidenceForRun':
        return await handleGetEvidenceForRun(args);

      case 'reg.summarizeEvidence':
        return await handleSummarizeEvidence(args);

      case 'reg.compareEvidence':
        return await handleCompareEvidence(args);

      case 'reg.getCriticalFindings':
        return await handleGetCriticalFindings(args);

      case 'reg.getMetrics':
        return handleGetMetrics();

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      content: [
        {
          type: 'text',
          text: `Error executing ${name}: ${errorMessage}`,
        },
      ],
    };
  }
});

/**
 * Tool: reg.getEvidenceForRun
 */
async function handleGetEvidenceForRun(args: any) {
  const { run_id, domain } = args;

  if (!run_id || !domain) {
    throw new Error('Missing required arguments: run_id and domain');
  }

  const request: EvidenceRequest = {
    runId: run_id,
    domain: domain as RegDomain,
  };

  // Add domain-specific context (would come from simulation metadata in production)
  if (domain === 'medical') {
    request.medical = {
      deviceType: 'neuromodulation',
      deviceClass: 3,
      region: 'US',
    };
  }

  const evidence = await regulatoryService.getEvidenceForRun(request);

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(evidence, null, 2),
      },
    ],
  };
}

/**
 * Tool: reg.summarizeEvidence
 */
async function handleSummarizeEvidence(args: any) {
  const { run_id } = args;

  if (!run_id) {
    throw new Error('Missing required argument: run_id');
  }

  // In production, fetch from cache/DB
  // For now, generate summary from fresh evidence request
  const request: EvidenceRequest = {
    runId: run_id,
    domain: 'medical', // Would detect from run metadata
  };

  const evidence = await regulatoryService.getEvidenceForRun(request);
  const summary = generateNaturalLanguageSummary(evidence);

  return {
    content: [
      {
        type: 'text',
        text: summary,
      },
    ],
  };
}

/**
 * Tool: reg.compareEvidence
 */
async function handleCompareEvidence(args: any) {
  const { run_ids } = args;

  if (!run_ids || !Array.isArray(run_ids) || run_ids.length < 2) {
    throw new Error('run_ids must be an array with at least 2 elements');
  }

  const comparison = await regulatoryService.compareEvidence(run_ids);

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(comparison, null, 2),
      },
    ],
  };
}

/**
 * Tool: reg.getCriticalFindings
 */
async function handleGetCriticalFindings(args: any) {
  const { run_id } = args;

  if (!run_id) {
    throw new Error('Missing required argument: run_id');
  }

  const request: EvidenceRequest = {
    runId: run_id,
    domain: 'medical',
  };

  const evidence = await regulatoryService.getEvidenceForRun(request);
  const criticalFindings = evidence.findings.filter(
    (f) => f.severity === 'critical'
  );

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(criticalFindings, null, 2),
      },
    ],
  };
}

/**
 * Tool: reg.getMetrics
 */
function handleGetMetrics() {
  const metrics = regulatoryService.getMetricsSummary();

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(metrics, null, 2),
      },
    ],
  };
}

/**
 * Generate natural language summary from evidence
 */
function generateNaturalLanguageSummary(evidence: RegulatoryEvidence): string {
  const { summary, findings } = evidence;

  if (findings.length === 0) {
    return `No regulatory findings for run ${evidence.runId}. All systems checked (${summary.systemsCovered.join(', ')}) returned clean results.`;
  }

  let text = `Run ${evidence.runId}: Found ${summary.totalFindings} regulatory findings across ${summary.systemsCovered.join(', ')}. `;

  if (summary.criticalCount > 0) {
    text += `⚠️ ${summary.criticalCount} CRITICAL issues detected. `;
    const criticalFindings = findings
      .filter((f) => f.severity === 'critical')
      .slice(0, 2);
    text += `Critical findings: ${criticalFindings.map((f) => f.summary).join('; ')}. `;
  } else {
    text += `No critical issues. `;
  }

  if (summary.warningCount > 0) {
    text += `${summary.warningCount} warnings. `;
  }

  if (summary.infoCount > 0) {
    text += `${summary.infoCount} informational items.`;
  }

  return text;
}

/**
 * Start the MCP server
 */
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error('Regulatory Evidence MCP server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error in main():', error);
  process.exit(1);
});
