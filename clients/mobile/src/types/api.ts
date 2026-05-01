export type ProcessRequest = {
	text?: string;
	audio_base64?: string;
	image_base64?: string;
	metadata?: Record<string, unknown>;
};

export type ProcessMetadata = {
	tts_url?: string;
	[key: string]: unknown;
};

export type ProcessResponse = {
	text: string;
	metadata?: ProcessMetadata;
};

export type Pose = {
	x: number;
	y: number;
	z: number;
	rotationX?: number;
	rotationY?: number;
	rotationZ?: number;
	rotationW?: number;
	confidence: number;
	accuracy?: number;
	timestamp?: number;
};

export type Destination = {
	id: string;
	name: string;
	description?: string;
	building?: string;
	floor?: string;
};

export type NavigationStartRequest = {
	destination: string;
	pose?: Pose;
};

export type NavigationStartResponse = {
	session_id: string;
	destination: string;
	total_steps: number;
	next_instruction: string;
};

export type NavigationStatus = {
	session_id: string;
	destination: string;
	current_step: number;
	total_steps: number;
	next_instruction: string;
	is_complete: boolean;
	updated_at?: string;
	distance_remaining?: number;
};

export type NavigationStep = {
	step_number: number;
	total_steps: number;
	instruction: string;
	waypoint?: string;
	distance?: number;
	turn_angle?: number;
};

export type NavigationNextResponse = {
	session_id: string;
	current_step: number;
	next_instruction: string;
	is_complete: boolean;
};

export type NavigationStopResponse = {
	session_id: string;
	stopped: boolean;
};

export type DestinationsResponse = {
	destinations: Destination[];
};

export type AudioDevice = {
	id: string;
	name: string;
	sample_rate?: number;
	channels?: number;
};

export type AudioDevicesResponse = {
	devices: AudioDevice[];
};
