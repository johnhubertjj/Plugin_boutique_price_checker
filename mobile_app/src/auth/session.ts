import * as SecureStore from "expo-secure-store";

import { SESSION_STORAGE_KEY } from "../config";

export async function saveSessionToken(token: string): Promise<void> {
  await SecureStore.setItemAsync(SESSION_STORAGE_KEY, token);
}

export async function loadSessionToken(): Promise<string | null> {
  return SecureStore.getItemAsync(SESSION_STORAGE_KEY);
}

export async function clearSessionToken(): Promise<void> {
  await SecureStore.deleteItemAsync(SESSION_STORAGE_KEY);
}
