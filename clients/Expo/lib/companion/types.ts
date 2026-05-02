export type ProcessMode = "quick" | "thinking";

export type ProcessRequest = {
	text?: string | null;
	audio_base64?: string | null;
	image_base64?: string | null;
	mode?: ProcessMode;
	client?: string;
	metadata?: Record<string, unknown>;
};

export type ProcessMetadata = {
	tts_url?: string;
	[key: string]: unknown;
};

export type ProcessResponse = {
	text: string;
	mode?: string;
	client?: string;
	tool_calls?: string[];
	metadata?: ProcessMetadata;
};
