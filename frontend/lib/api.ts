import { CollectorReport, DiagnoseResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function runDiagnosis(
  report: CollectorReport,
  rewriteWithAi: boolean = true
): Promise<DiagnoseResponse> {
  const url = `${API_BASE}/diagnose?rewrite=${rewriteWithAi}`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(report),
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Diagnosis API request failed (${response.status}): ${errText}`);
  }

  return await response.json();
}
