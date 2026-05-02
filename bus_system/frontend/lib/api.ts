export type ApiEnvelope<T> = {
	ok: boolean;
	message: string;
	messages: {
		en: string;
		ar: string;
	};
	lang: string;
	data: T;
};

export type BusLocationData = {
	route: string;
	location: {
		lat: number;
		lng: number;
	};
	speed_kmh: number;
	traffic_level: number;
	current_passengers: number;
	total_seats: number;
	occupancy_rate: number;
	predicted_passengers: number;
	status: string;
	last_stop: string;
	next_stop: string;
	route_progress_percent: number;
	estimated_eta_minutes: number;
	route_points: Array<{ lat: number; lng: number }>;
	stops: Array<{ index: number; name: string }>;
};

const API_BASE =
	process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(
	path: string,
	options?: RequestInit,
	lang: "en" | "ar" = "en",
): Promise<ApiEnvelope<T>> {
	const separator = path.includes("?") ? "&" : "?";
	const response = await fetch(`${API_BASE}${path}${separator}lang=${lang}`, {
		...options,
		headers: {
			"Content-Type": "application/json",
			...(options?.headers ?? {}),
		},
		cache: "no-store",
	});

	if (!response.ok) {
		const text = await response.text();
		throw new Error(text || `Request failed (${response.status})`);
	}

	return (await response.json()) as ApiEnvelope<T>;
}

export function getBusLocation(lang: "en" | "ar" = "en") {
	return request<BusLocationData>("/bus/location", undefined, lang);
}

export function getBusCapacity(lang: "en" | "ar" = "en") {
	return request<{
		total_seats: number;
		current_passengers: number;
		available_seats: number;
		occupancy_rate: number;
	}>("/bus/capacity", undefined, lang);
}

export function getBusCapacityPrediction(lang: "en" | "ar" = "en") {
	return request<{
		total_seats: number;
		predicted_passengers: number;
		predicted_available_seats: number;
		probability_bus_full: number;
	}>("/bus/capacity/prediction", undefined, lang);
}

export function getPredictedEta(lang: "en" | "ar" = "en") {
	return request<{
		predicted_eta_minutes: number;
		traffic_level: number;
		incident_impact_minutes: number;
		model: string;
	}>("/bus/eta/predicted", undefined, lang);
}

export function getStudents(lang: "en" | "ar" = "en") {
	return request<{
		students: Array<{
			id: number;
			name: string;
			home_location: string;
			home: { lat: number; lng: number };
			wallet_balance: number;
			subscription_status: string;
		}>;
	}>("/students", undefined, lang);
}

export function getWalletBalance(studentId: number, lang: "en" | "ar" = "en") {
	return request<{
		student_id: number;
		student_name: string;
		balance: number;
		subscription_status: string;
		subscription_expires_at: string | null;
	}>(`/wallet/balance?student_id=${studentId}`, undefined, lang);
}

export function getWalletHistory(studentId: number, lang: "en" | "ar" = "en") {
	return request<{
		student_id: number;
		student_name: string;
		balance: number;
		transactions: Array<{
			id: number;
			type: string;
			amount: number;
			status: string;
			description: string;
			created_at: string;
		}>;
	}>(`/wallet/history?student_id=${studentId}`, undefined, lang);
}

export function addWalletBalance(
	student_id: number,
	amount: number,
	lang: "en" | "ar" = "en",
) {
	return request<{
		student_id: number;
		new_balance: number;
		transaction_id: number;
	}>(
		"/wallet/add",
		{
			method: "POST",
			body: JSON.stringify({ student_id, amount }),
		},
		lang,
	);
}

export function payWallet(
	student_id: number,
	amount: number,
	payment_type: "trip" | "subscription",
	force_fail = false,
	lang: "en" | "ar" = "en",
) {
	return request<{
		student_id: number;
		remaining_balance: number;
		transaction_id: number;
		status: string;
		description: string;
		payment_type: string;
	}>(
		"/wallet/pay",
		{
			method: "POST",
			body: JSON.stringify({ student_id, amount, payment_type, force_fail }),
		},
		lang,
	);
}

export function subscribeStudent(
	studentId: number,
	months: number,
	lang: "en" | "ar" = "en",
) {
	return request<{
		student_id: number;
		status: string;
		months: number;
		charged: number;
		new_balance: number;
		subscription_expires_at: string | null;
		transaction_id: number;
	}>(
		`/students/${studentId}/subscribe`,
		{
			method: "POST",
			body: JSON.stringify({ months }),
		},
		lang,
	);
}

export function getActiveReports(lang: "en" | "ar" = "en") {
	return request<{ count: number; incidents: Array<Record<string, unknown>> }>(
		"/reports/active",
		undefined,
		lang,
	);
}

export function postIncident(
	payload: {
		reporter_role: "student" | "driver" | "system";
		reporter_name?: string;
		incident_type:
			| "traffic_jam"
			| "bus_full"
			| "breakdown"
			| "early_arrival"
			| "delay";
		description: string;
		eta_impact_minutes?: number;
	},
	lang: "en" | "ar" = "en",
) {
	return request<Record<string, unknown>>(
		"/report/incident",
		{
			method: "POST",
			body: JSON.stringify(payload),
		},
		lang,
	);
}

export function backendBaseUrl() {
	return API_BASE;
}
