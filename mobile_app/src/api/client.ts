import { API_BASE_URL } from "../config";
import type { AuthFlowResponse, AuthTokenResponse, PriceCheckRun, User, WatchlistItem } from "../types/api";

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  token?: string | null;
};

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  const text = await response.text();
  const json = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const detail = json?.detail ?? `${response.status} ${response.statusText}`;
    throw new ApiError(response.status, detail);
  }

  return json as T;
}

export async function getMe(token: string): Promise<User> {
  return request<User>("/me", { token });
}

export async function startRegister(email: string, phoneNumber: string): Promise<AuthFlowResponse> {
  return request<AuthFlowResponse>("/auth/register/start", {
    method: "POST",
    body: { email, phone_number: phoneNumber },
  });
}

export async function verifyEmailCode(email: string, code: string): Promise<AuthFlowResponse> {
  return request<AuthFlowResponse>("/auth/register/verify-email", {
    method: "POST",
    body: { email, code },
  });
}

export async function verifyPhoneCode(email: string, code: string): Promise<AuthTokenResponse> {
  return request<AuthTokenResponse>("/auth/register/verify-phone", {
    method: "POST",
    body: { email, code },
  });
}

export async function startLogin(email: string): Promise<AuthFlowResponse> {
  return request<AuthFlowResponse>("/auth/login/start", {
    method: "POST",
    body: { email },
  });
}

export async function verifyLoginCode(email: string, code: string): Promise<AuthTokenResponse> {
  return request<AuthTokenResponse>("/auth/login/verify", {
    method: "POST",
    body: { email, code },
  });
}

export async function logout(token: string): Promise<void> {
  await request<null>("/auth/logout", { method: "POST", token });
}

export async function listWatchlistItems(token: string): Promise<WatchlistItem[]> {
  return request<WatchlistItem[]>("/me/watchlist-items", { token });
}

export async function createWatchlistItem(token: string, productUrl: string, threshold: number): Promise<WatchlistItem> {
  return request<WatchlistItem>("/me/watchlist-items", {
    method: "POST",
    token,
    body: { product_url: productUrl, threshold },
  });
}

export async function runWatchlistCheck(token: string, itemId: number): Promise<PriceCheckRun> {
  return request<PriceCheckRun>(`/me/watchlist-items/${itemId}/check`, {
    method: "POST",
    token,
  });
}

export async function deleteWatchlistItem(token: string, itemId: number): Promise<void> {
  await request<null>(`/me/watchlist-items/${itemId}`, {
    method: "DELETE",
    token,
  });
}
