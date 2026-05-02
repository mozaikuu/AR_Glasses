import type { ProcessRequest, ProcessResponse } from "@/lib/companion/types";
import { getApiKey, getBackendUrl, normalizeBackendUrl } from "@/lib/companion/config";

export function resolveAbsoluteUrl(baseUrl: string, maybeRelative: string): string {
	const trimmed = maybeRelative.trim();
	if (!trimmed) {
		return trimmed;
	}
	if (/^https?:\/\//i.test(trimmed)) {
		return trimmed;
	}
	const base = baseUrl.replace(/\/+$/, "");
	const path = trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
	return `${base}${path}`;
}

function looksLikeHtml(snippet: string): boolean {
	return /<\s*html[\s>]/i.test(snippet) || /<\s*!doctype\s+html/i.test(snippet);
}

export function formatCompanionHttpError(
	status: number,
	bodySnippet: string,
	requestUrl: string,
): string {
	const trimmed = bodySnippet.trim();
	let msg = `HTTP ${status} (${requestUrl})`;
	if (trimmed) {
		msg += `\n${trimmed.slice(0, 280)}`;
	}
	if (status === 403) {
		msg +=
			"\n\nForbidden: you may be hitting the wrong host/port (not the FastAPI gateway), a proxy or CDN is blocking the request, or X-API-Key does not match your server. On a physical phone, use your PC LAN URL (not 127.0.0.1).";
	}
	if (looksLikeHtml(trimmed)) {
		msg +=
			"\n\nResponse looks like HTML — often a login page, static host, or Expo dev server instead of the gateway.";
	}
	return msg;
}

export async function testCompanionGateway(
	baseURL: string,
	apiKey?: string | null,
	options?: { timeoutMs?: number },
): Promise<{ ok: boolean; status: number; detail: string }> {
	const base = normalizeBackendUrl(baseURL);
	const url = `${base}/`;
	const timeoutMs = options?.timeoutMs ?? 15_000;

	const controller = new AbortController();
	const timer = setTimeout(() => controller.abort(), timeoutMs);

	const headers: Record<string, string> = {
		Accept: "application/json",
	};
	if (apiKey?.trim()) {
		headers["X-API-Key"] = apiKey.trim();
	}

	try {
		const res = await fetch(url, {
			method: "GET",
			headers,
			signal: controller.signal,
		});
		const text = await res.text().catch(() => "");
		if (!res.ok) {
			return {
				ok: false,
				status: res.status,
				detail: formatCompanionHttpError(res.status, text, url),
			};
		}
		let summary = text.slice(0, 200);
		try {
			const j = JSON.parse(text) as Record<string, unknown>;
			summary =
				(typeof j.status === "string" ? j.status : "") ||
				(typeof j.service === "string" ? j.service : "") ||
				summary;
		} catch {
			// not JSON
		}
		return {
			ok: true,
			status: res.status,
			detail: `Gateway reachable (${url})\n${summary}`,
		};
	} catch (e) {
		const err = e instanceof Error ? e.message : String(e);
		return {
			ok: false,
			status: 0,
			detail: `Request failed (${url})\n${err}`,
		};
	} finally {
		clearTimeout(timer);
	}
}

export async function processCompanion(
	payload: ProcessRequest,
	options?: { timeoutMs?: number },
): Promise<ProcessResponse> {
	const baseURL = await getBackendUrl();
	const apiKey = await getApiKey();
	const timeoutMs = options?.timeoutMs ?? 120_000;

	const controller = new AbortController();
	const timer = setTimeout(() => controller.abort(), timeoutMs);

	const headers: Record<string, string> = {
		"Content-Type": "application/json",
		Accept: "application/json",
	};
	if (apiKey) {
		headers["X-API-Key"] = apiKey;
	}

	const body: ProcessRequest = {
		mode: "quick",
		client: "expo_companion",
		...payload,
	};

	const requestUrl = `${baseURL.replace(/\/+$/, "")}/process`;

	try {
		const res = await fetch(requestUrl, {
			method: "POST",
			headers,
			body: JSON.stringify(body),
			signal: controller.signal,
		});
		if (!res.ok) {
			const text = await res.text().catch(() => "");
			throw new Error(formatCompanionHttpError(res.status, text, requestUrl));
		}
		return (await res.json()) as ProcessResponse;
	} finally {
		clearTimeout(timer);
	}
}
