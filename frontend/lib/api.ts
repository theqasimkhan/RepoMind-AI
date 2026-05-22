import { fetchWithAuth } from "@/lib/auth";
import {
  AnalysisJobStartResponse,
  AnalysisJobStatusResponse,
  AnalysisRequest,
  AnalysisResponse,
  ChatQueryRequest,
  ChatQueryResponse,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

if (!API_BASE_URL) {
  console.warn(
    "Warning: NEXT_PUBLIC_API_BASE_URL is not defined. " +
    "API requests will likely fail. Ensure it is set in your .env.local file."
  );
}

async function handleResponseError(response: Response, defaultMessage: string) {
  const errorData = await response.json().catch(() => ({}));
  let errorMessage = defaultMessage;
  if (errorData.detail) {
    errorMessage = typeof errorData.detail === "string" 
      ? errorData.detail 
      : JSON.stringify(errorData.detail);
  }
  throw new Error(errorMessage);
}

export async function analyzeRepository(
  payload: AnalysisRequest
): Promise<AnalysisResponse> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/repositories/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  if (!response.ok) {
    await handleResponseError(response, "Failed to analyze repository");
  }

  return (await response.json()) as AnalysisResponse;
}

export async function startRepositoryAnalysis(
  payload: AnalysisRequest
): Promise<AnalysisJobStartResponse> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/repositories/analyze/async`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });
  if (!response.ok) {
    await handleResponseError(response, "Failed to start analysis job");
  }
  return (await response.json()) as AnalysisJobStartResponse;
}

export async function getRepositoryAnalysisStatus(
  jobId: string
): Promise<AnalysisJobStatusResponse> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/repositories/analyze/async/${jobId}`, {
    method: "GET",
    cache: "no-store",
  });
  if (!response.ok) {
    await handleResponseError(response, "Failed to fetch analysis status");
  }
  return (await response.json()) as AnalysisJobStatusResponse;
}

export async function listRepositoryAnalysisJobs(
  limit = 20
): Promise<AnalysisJobStatusResponse[]> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/repositories/analyze/async?limit=${limit}`, {
    method: "GET",
    cache: "no-store",
  });
  if (!response.ok) {
    await handleResponseError(response, "Failed to fetch analysis jobs");
  }
  const payload = (await response.json()) as { jobs: AnalysisJobStatusResponse[] };
  return payload.jobs;
}

export async function queryRepositoryChat(
  payload: ChatQueryRequest
): Promise<ChatQueryResponse> {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/chat/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  if (!response.ok) {
    await handleResponseError(response, "Failed to query repository chat");
  }

  return (await response.json()) as ChatQueryResponse;
}

export async function getLatestRepositoryAnalysis(repoUrl: string): Promise<AnalysisResponse | null> {
  const url = `${API_BASE_URL}/api/v1/repositories/analysis/latest?repo_url=${encodeURIComponent(repoUrl)}`;
  const response = await fetchWithAuth(url, { method: "GET", cache: "no-store" });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    await handleResponseError(response, "Failed to fetch latest repository analysis");
  }
  return (await response.json()) as AnalysisResponse;
}
