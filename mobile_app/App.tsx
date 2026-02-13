import { StatusBar } from "expo-status-bar";
import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import {
  ApiError,
  createWatchlistItem,
  deleteWatchlistItem,
  getMe,
  listWatchlistItems,
  logout,
  runWatchlistCheck,
  startLogin,
  startRegister,
  verifyEmailCode,
  verifyLoginCode,
  verifyPhoneCode,
} from "./src/api/client";
import { clearSessionToken, loadSessionToken, saveSessionToken } from "./src/auth/session";
import type { User, WatchlistItem } from "./src/types/api";

function extractErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unexpected error";
}

function formatPrice(item: WatchlistItem): string {
  if (item.last_price === null) {
    return "-";
  }
  return `${item.last_currency ?? ""}${item.last_price}`;
}

function formatDate(value: string | null): string {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

export default function App(): JSX.Element {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [info, setInfo] = useState<string>("");
  const [devCode, setDevCode] = useState<string>("");

  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPhone, setRegisterPhone] = useState("");
  const [registerEmailCode, setRegisterEmailCode] = useState("");
  const [registerPhoneCode, setRegisterPhoneCode] = useState("");
  const [authEmailContext, setAuthEmailContext] = useState("");

  const [loginEmail, setLoginEmail] = useState("");
  const [loginCode, setLoginCode] = useState("");

  const [newUrl, setNewUrl] = useState("");
  const [newThreshold, setNewThreshold] = useState("");

  const isAuthenticated = useMemo(() => Boolean(token && user), [token, user]);

  useEffect(() => {
    async function bootstrap() {
      try {
        const storedToken = await loadSessionToken();
        if (!storedToken) {
          return;
        }
        const me = await getMe(storedToken);
        setToken(storedToken);
        setUser(me);
        const watchlist = await listWatchlistItems(storedToken);
        setItems(watchlist);
      } catch (error) {
        await clearSessionToken();
        setInfo(`Session reset: ${extractErrorMessage(error)}`);
      }
    }

    void bootstrap();
  }, []);

  async function refreshWatchlist(activeToken: string) {
    const watchlist = await listWatchlistItems(activeToken);
    setItems(watchlist);
  }

  async function applySession(nextToken: string) {
    await saveSessionToken(nextToken);
    setToken(nextToken);
    const me = await getMe(nextToken);
    setUser(me);
    await refreshWatchlist(nextToken);
  }

  async function handleRegisterStart() {
    setBusy(true);
    try {
      const email = registerEmail.trim();
      const phone = registerPhone.trim();
      const response = await startRegister(email, phone);
      setAuthEmailContext(email);
      setLoginEmail(email);
      setDevCode(response.dev_code ?? "");
      setInfo(response.message);
    } catch (error) {
      Alert.alert("Registration error", extractErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleVerifyEmail() {
    setBusy(true);
    try {
      const email = authEmailContext || registerEmail.trim();
      const response = await verifyEmailCode(email, registerEmailCode.trim());
      setDevCode(response.dev_code ?? "");
      setInfo(response.message);
    } catch (error) {
      Alert.alert("Verify email error", extractErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleVerifyPhone() {
    setBusy(true);
    try {
      const email = authEmailContext || registerEmail.trim();
      const response = await verifyPhoneCode(email, registerPhoneCode.trim());
      await applySession(response.access_token);
      setDevCode("");
      setInfo("Registration complete.");
      setRegisterEmailCode("");
      setRegisterPhoneCode("");
    } catch (error) {
      Alert.alert("Verify phone error", extractErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleLoginStart() {
    setBusy(true);
    try {
      const email = loginEmail.trim();
      const response = await startLogin(email);
      setAuthEmailContext(email);
      setDevCode(response.dev_code ?? "");
      setInfo(response.message);
    } catch (error) {
      Alert.alert("Login start error", extractErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleLoginVerify() {
    setBusy(true);
    try {
      const email = authEmailContext || loginEmail.trim();
      const response = await verifyLoginCode(email, loginCode.trim());
      await applySession(response.access_token);
      setDevCode("");
      setInfo("Authenticated.");
      setLoginCode("");
    } catch (error) {
      Alert.alert("Login verify error", extractErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateItem() {
    if (!token) {
      return;
    }
    setBusy(true);
    try {
      const threshold = Number(newThreshold);
      if (!Number.isFinite(threshold) || threshold <= 0) {
        throw new Error("Threshold must be a positive number");
      }
      await createWatchlistItem(token, newUrl.trim(), threshold);
      setNewUrl("");
      setNewThreshold("");
      await refreshWatchlist(token);
      setInfo("Watchlist item added.");
    } catch (error) {
      Alert.alert("Add item error", extractErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleRunCheck(itemId: number) {
    if (!token) {
      return;
    }
    setBusy(true);
    try {
      await runWatchlistCheck(token, itemId);
      await refreshWatchlist(token);
      setInfo(`Check complete for item ${itemId}.`);
    } catch (error) {
      Alert.alert("Run check error", extractErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleDeleteItem(itemId: number) {
    if (!token) {
      return;
    }
    setBusy(true);
    try {
      await deleteWatchlistItem(token, itemId);
      await refreshWatchlist(token);
      setInfo(`Deleted item ${itemId}.`);
    } catch (error) {
      Alert.alert("Delete item error", extractErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleLogout() {
    const activeToken = token;
    try {
      if (activeToken) {
        await logout(activeToken);
      }
    } catch (_error) {
      // Even if remote logout fails, clear local session.
    }

    await clearSessionToken();
    setToken(null);
    setUser(null);
    setItems([]);
    setDevCode("");
    setInfo("Logged out.");
  }

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar style="dark" />
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Plugin Boutique Mobile</Text>
        <Text style={styles.subtitle}>API-connected starter app (Expo + React Native)</Text>

        {busy ? <ActivityIndicator color="#0f766e" /> : null}

        {info ? <Text style={styles.info}>{info}</Text> : null}
        {devCode ? <Text style={styles.devCode}>Dev OTP: {devCode}</Text> : null}

        {!isAuthenticated ? (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Register (Email + Phone 2FA)</Text>
            <TextInput
              style={styles.input}
              autoCapitalize="none"
              keyboardType="email-address"
              placeholder="Email"
              value={registerEmail}
              onChangeText={setRegisterEmail}
            />
            <TextInput
              style={styles.input}
              keyboardType="phone-pad"
              placeholder="Phone (+15551234567)"
              value={registerPhone}
              onChangeText={setRegisterPhone}
            />
            <Pressable style={styles.button} onPress={handleRegisterStart}>
              <Text style={styles.buttonText}>Start Registration</Text>
            </Pressable>

            <TextInput
              style={styles.input}
              placeholder="Email OTP"
              value={registerEmailCode}
              onChangeText={setRegisterEmailCode}
            />
            <Pressable style={styles.button} onPress={handleVerifyEmail}>
              <Text style={styles.buttonText}>Verify Email</Text>
            </Pressable>

            <TextInput
              style={styles.input}
              placeholder="Phone OTP"
              value={registerPhoneCode}
              onChangeText={setRegisterPhoneCode}
            />
            <Pressable style={styles.button} onPress={handleVerifyPhone}>
              <Text style={styles.buttonText}>Verify Phone</Text>
            </Pressable>

            <Text style={styles.sectionTitle}>Login</Text>
            <TextInput
              style={styles.input}
              autoCapitalize="none"
              keyboardType="email-address"
              placeholder="Email"
              value={loginEmail}
              onChangeText={setLoginEmail}
            />
            <Pressable style={styles.button} onPress={handleLoginStart}>
              <Text style={styles.buttonText}>Send Login OTP</Text>
            </Pressable>

            <TextInput
              style={styles.input}
              placeholder="Login OTP"
              value={loginCode}
              onChangeText={setLoginCode}
            />
            <Pressable style={styles.button} onPress={handleLoginVerify}>
              <Text style={styles.buttonText}>Verify Login</Text>
            </Pressable>
          </View>
        ) : (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Signed in as {user?.email}</Text>
            <View style={styles.row}>
              <Pressable
                style={[styles.button, styles.halfButton]}
                onPress={() => (token ? refreshWatchlist(token).catch((error) => Alert.alert("Refresh", extractErrorMessage(error))) : null)}
              >
                <Text style={styles.buttonText}>Refresh</Text>
              </Pressable>
              <Pressable style={[styles.button, styles.halfButton, styles.logoutButton]} onPress={handleLogout}>
                <Text style={styles.buttonText}>Logout</Text>
              </Pressable>
            </View>

            <Text style={styles.sectionTitle}>Add Watchlist Item</Text>
            <TextInput
              style={styles.input}
              autoCapitalize="none"
              placeholder="Product URL"
              value={newUrl}
              onChangeText={setNewUrl}
            />
            <TextInput
              style={styles.input}
              keyboardType="decimal-pad"
              placeholder="Threshold"
              value={newThreshold}
              onChangeText={setNewThreshold}
            />
            <Pressable style={styles.button} onPress={handleCreateItem}>
              <Text style={styles.buttonText}>Add Item</Text>
            </Pressable>

            <Text style={styles.sectionTitle}>My Watchlist</Text>
            {items.length === 0 ? <Text style={styles.meta}>No watchlist items yet.</Text> : null}
            {items.map((item) => (
              <View key={item.id} style={styles.card}>
                <Text style={styles.cardTitle}>#{item.id}</Text>
                <Text style={styles.meta}>{item.product_url}</Text>
                <Text style={styles.meta}>Threshold: {item.threshold}</Text>
                <Text style={styles.meta}>Last price: {formatPrice(item)}</Text>
                <Text style={styles.meta}>Last checked: {formatDate(item.last_checked_at)}</Text>
                <View style={styles.row}>
                  <Pressable style={[styles.button, styles.halfButton]} onPress={() => handleRunCheck(item.id)}>
                    <Text style={styles.buttonText}>Run Check</Text>
                  </Pressable>
                  <Pressable
                    style={[styles.button, styles.halfButton, styles.deleteButton]}
                    onPress={() => handleDeleteItem(item.id)}
                  >
                    <Text style={styles.buttonText}>Remove</Text>
                  </Pressable>
                </View>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#f2f6f5",
  },
  container: {
    padding: 16,
    gap: 10,
  },
  title: {
    fontSize: 28,
    fontWeight: "700",
    color: "#0f172a",
  },
  subtitle: {
    color: "#334155",
    marginBottom: 8,
  },
  info: {
    color: "#0f766e",
  },
  devCode: {
    color: "#7c3aed",
    fontWeight: "600",
  },
  section: {
    backgroundColor: "#ffffff",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#d5dfdd",
    padding: 12,
    gap: 10,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#111827",
    marginTop: 4,
  },
  input: {
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 9,
    backgroundColor: "#ffffff",
  },
  button: {
    borderRadius: 10,
    backgroundColor: "#0f766e",
    paddingVertical: 10,
    alignItems: "center",
  },
  buttonText: {
    color: "#ffffff",
    fontWeight: "600",
  },
  row: {
    flexDirection: "row",
    gap: 8,
  },
  halfButton: {
    flex: 1,
  },
  logoutButton: {
    backgroundColor: "#334155",
  },
  deleteButton: {
    backgroundColor: "#b91c1c",
  },
  card: {
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#d7dfe8",
    backgroundColor: "#fbfdff",
    padding: 10,
    gap: 4,
  },
  cardTitle: {
    fontWeight: "600",
    color: "#0f172a",
  },
  meta: {
    color: "#475569",
    fontSize: 13,
  },
});
