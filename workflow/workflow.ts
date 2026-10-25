import {
  consensusIdenticalAggregation,
  cre,
  getNetwork,
  prepareReportRequest,
  TxStatus,
  bytesToHex,
  type CronPayload,
  type HTTPSendRequester,
  type Runtime,
} from "@chainlink/cre-sdk";
import { z } from "zod";
import codeMap from "./src/codeMap.json";
import { canonicalDocs, legalsUrl, masterUrl } from "./src/acris";
import { buildReport } from "./src/report";
import type { AcrisDoc } from "./src/classify";

export const configSchema = z.object({
  schedule: z.string(),
  bbl: z.object({ borough: z.number().int().min(1).max(5), block: z.number().int(), lot: z.number().int() }),
  tokenAddress: z.string(),
  chainSelectorName: z.string(),
  gasLimit: z.string(),
});
type Config = z.infer<typeof configSchema>;

const CHUNK = 80; // keep Socrata URLs short for busy lots

// Runs on EVERY node independently. Returns canonical JSON so DON consensus is on the exact doc set.
const fetchDocs = (sendRequester: HTTPSendRequester, config: Config): string => {
  const get = (url: string): any[] => {
    const r = sendRequester.sendRequest({ method: "GET", url }).result();
    if (r.statusCode !== 200) throw new Error(`ACRIS request failed: ${r.statusCode}`); // fail static: no report
    return JSON.parse(Buffer.from(r.body).toString("utf-8"));
  };
  const legals = get(legalsUrl(config.bbl as any));
  const master: any[] = [];
  for (let i = 0; i < legals.length; i += CHUNK)
    master.push(...get(masterUrl(legals.slice(i, i + CHUNK).map((l) => l.document_id))));
  return JSON.stringify(canonicalDocs(legals, master));
};

export const onCronTrigger = (runtime: Runtime<Config>, payload: CronPayload): string => {
  if (!payload.scheduledExecutionTime) throw new Error("Scheduled execution time is required");

  const docsJson = new cre.capabilities.HTTPClient()
    .sendRequest(runtime, fetchDocs, consensusIdenticalAggregation<string>())(runtime.config)
    .result();
  const docs: AcrisDoc[] = JSON.parse(docsJson);

  const { payload: reportPayload, adverse } = buildReport(runtime.config.bbl as any, docs, codeMap);
  runtime.log(`ACRIS docs=${docs.length} adverse=${adverse.map((d) => `${d.documentId}:${d.docType}`).join(",") || "none"}`);

  const network = getNetwork({ chainFamily: "evm", chainSelectorName: runtime.config.chainSelectorName, isTestnet: true });
  if (!network) throw new Error(`Network not found: ${runtime.config.chainSelectorName}`);
  const evmClient = new cre.capabilities.EVMClient(network.chainSelector.selector);

  const report = runtime.report(prepareReportRequest(reportPayload)).result();
  const resp = evmClient
    .writeReport(runtime, { receiver: runtime.config.tokenAddress, report, gasConfig: { gasLimit: runtime.config.gasLimit } })
    .result();
  if (resp.txStatus !== TxStatus.SUCCESS) throw new Error(`writeReport failed: ${resp.errorMessage || resp.txStatus}`);
  const tx = bytesToHex(resp.txHash || new Uint8Array(32));
  runtime.log(`report written tx=${tx}`);
  return tx;
};

export function initWorkflow(config: Config) {
  return [cre.handler(new cre.capabilities.CronCapability().trigger({ schedule: config.schedule }), onCronTrigger)];
}
