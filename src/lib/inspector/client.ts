import { ledgerOp } from "./engine";
import { useInspector } from "./store";

function toBase64(bytes: Uint8Array) {
  let binary = "";
  const size = 0x8000;
  for (let index = 0; index < bytes.length; index += size) {
    binary += String.fromCharCode(...bytes.subarray(index, index + size));
  }
  return btoa(binary);
}

function currentRequest() {
  const state = useInspector.getState();
  return { ruleSetId: state.ruleSetId, overrides: state.overrides, model: state.model };
}

export async function inspectNamed(name: string, bytes: Uint8Array) {
  const store = useInspector.getState();
  store.setLoading(true);
  store.setLoadError(null);
  try {
    const { ruleSetId, overrides } = currentRequest();
    const result = await ledgerOp({
      data: { op: "inspect", fileName: name, dataBase64: toBase64(bytes), ruleSetId, overrides },
    });
    if (!result.ok || !result.model || !result.findings) {
      throw new Error(result.message || "Python inspection failed.");
    }
    useInspector.getState().setReport(result.model, result.findings);
  } catch (error) {
    useInspector.getState().setLoadError(error instanceof Error ? error.message : "Python inspection failed.");
  } finally {
    useInspector.getState().setLoading(false);
  }
}

export async function refreshFindings() {
  const { model, ruleSetId, overrides } = currentRequest();
  if (!model) return;
  const result = await ledgerOp({ data: { op: "checks", model, ruleSetId, overrides } });
  if (result.ok && result.findings) useInspector.getState().setFindings(result.findings);
}

export async function reviewCandidate(id: string, status: "unreviewed" | "confirmed" | "rejected") {
  const { model, ruleSetId, overrides } = currentRequest();
  if (!model) return;
  const result = await ledgerOp({ data: { op: "candidate", model, ruleSetId, overrides, candidateId: id, status } });
  if (result.ok && result.model && result.findings) {
    useInspector.getState().setReport(result.model, result.findings, { keepPlace: true });
  }
}

export async function confirmHighCandidates() {
  const { model, ruleSetId, overrides } = currentRequest();
  if (!model) return;
  const result = await ledgerOp({ data: { op: "confirm-high", model, ruleSetId, overrides } });
  if (result.ok && result.model && result.findings) {
    useInspector.getState().setReport(result.model, result.findings, { keepPlace: true });
  }
}
