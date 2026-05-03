import AsyncStorage from "@react-native-async-storage/async-storage";

export const STORAGE_ACTIVE_BUILDING_JSON = "indoor_nav_active_building_json_v1";
export const STORAGE_ACTIVE_CAMPUS_JSON = "indoor_nav_active_campus_json_v1";
export const STORAGE_NAV_MODE = "indoor_nav_mode_v1"; // "indoor" | "campus"

export async function loadString(key: string): Promise<string | null> {
	try {
		return await AsyncStorage.getItem(key);
	} catch {
		return null;
	}
}

export async function saveString(key: string, value: string): Promise<void> {
	await AsyncStorage.setItem(key, value);
}

export async function removeKey(key: string): Promise<void> {
	await AsyncStorage.removeItem(key);
}
