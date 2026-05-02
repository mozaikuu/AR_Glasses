/**
 * Heuristic: when the user query is short or clearly visual, attach a camera frame
 * so the backend can use vision (via MCP when configured) or at least disambiguate.
 */
const VISUAL_CUES = [
	"what is this",
	"what's this",
	"what am i looking at",
	"what i'm looking at",
	"what i am looking at",
	"what do you see",
	"can you read this",
	"read this",
	"read the",
	"translate this",
	"what does this say",
	"what is in front",
	"what is in front of me",
	"describe what you see",
	"describe what i am looking at",
	"describe what i'm looking at",
	"look at this",
	"identify this",
	"where am i",
	"what building",
	"what room",
	"help me find",
];

export function shouldCaptureContext(question: string): boolean {
	const q = question.trim().toLowerCase();
	if (!q) {
		return false;
	}

	for (const cue of VISUAL_CUES) {
		if (q.includes(cue)) {
			return true;
		}
	}

	// Very short queries are often underspecified
	const letters = q.replace(/[^a-z0-9]/gi, "");
	if (letters.length > 0 && letters.length <= 8 && q.split(/\s+/).length <= 3) {
		return true;
	}

	return false;
}
