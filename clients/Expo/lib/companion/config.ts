import AsyncStorage from "@react-native-async-storage/async-storage";

const STORAGE_BACKEND_URL = "companion_backend_url";
const STORAGE_API_KEY = "companion_api_key";

const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";

/** Trim, strip trailing slashes, default scheme to http if missing. */
export function normalizeBackendUrl(url: string): string {
	let u = url.trim().replace(/\/+$/, "");
	if (!u) {
		return DEFAULT_BACKEND_URL;
	}
	if (!/^https?:\/\//i.test(u)) {
		u = `http://${u}`;
	}
	return u.replace(/\/+$/, "");
}

export async function getBackendUrl(): Promise<string> {
	try {
		const v = await AsyncStorage.getItem(STORAGE_BACKEND_URL);
		const raw = v?.trim();
		return raw ? normalizeBackendUrl(raw) : DEFAULT_BACKEND_URL;
	} catch {
		return DEFAULT_BACKEND_URL;
	}
}

export async function setBackendUrl(url: string): Promise<void> {
	await AsyncStorage.setItem(
		STORAGE_BACKEND_URL,
		normalizeBackendUrl(url),
	);
}

export async function getApiKey(): Promise<string | null> {
	try {
		const v = await AsyncStorage.getItem(STORAGE_API_KEY);
		const t = v?.trim();
		return t?.length ? t : null;
	} catch {
		return null;
	}
}

export async function setApiKey(key: string | null): Promise<void> {
	if (!key?.trim()) {
		await AsyncStorage.removeItem(STORAGE_API_KEY);
		return;
	}
	await AsyncStorage.setItem(STORAGE_API_KEY, key.trim());
}

export function getDefaultBackendUrl(): string {
	return DEFAULT_BACKEND_URL;
}
