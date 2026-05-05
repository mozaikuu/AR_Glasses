import { Platform } from "react-native";
import { Directory, File, Paths } from "expo-file-system";

const GLB_MAGIC = 0x46546c67;
const CHUNK_JSON = 0x4e4f534a; // "JSON"
const CHUNK_BIN = 0x004e4942; // "BIN\0"

type GltfImage = {
	uri?: string;
	bufferView?: number;
	mimeType?: string;
	name?: string;
};

type GltfBufferView = {
	buffer?: number;
	byteOffset?: number;
	byteLength: number;
};

type GltfRoot = {
	images?: GltfImage[];
	bufferViews?: GltfBufferView[];
};

function uint8ToBase64(bytes: Uint8Array): string {
	let binary = "";
	const chunk = 0x8000;
	for (let i = 0; i < bytes.length; i += chunk) {
		binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
	}
	const enc = globalThis as typeof globalThis & { btoa?: (s: string) => string };
	if (typeof enc.btoa !== "function") {
		throw new Error("btoa is not available for GLB texture extraction.");
	}
	return enc.btoa(binary);
}

function sniffImageExt(slice: Uint8Array, mime: string | undefined): string {
	if (mime) {
		if (mime.includes("jpeg") || mime.includes("jpg")) {
			return ".jpg";
		}
		if (mime.includes("webp")) {
			return ".webp";
		}
		if (mime.includes("png")) {
			return ".png";
		}
	}
	if (slice.length >= 3 && slice[0] === 0xff && slice[1] === 0xd8 && slice[2] === 0xff) {
		return ".jpg";
	}
	if (slice.length >= 4 && slice[0] === 0x89 && slice[1] === 0x50 && slice[2] === 0x4e && slice[3] === 0x47) {
		return ".png";
	}
	if (slice.length >= 12 && slice[0] === 0x52 && slice[1] === 0x49 && slice[2] === 0x46 && slice[3] === 0x46) {
		return ".webp";
	}
	return ".png";
}

function padJsonChunk(jsonStr: string): Uint8Array {
	const encoded = new TextEncoder().encode(jsonStr);
	const pad = (4 - (encoded.byteLength % 4)) % 4;
	const out = new Uint8Array(encoded.byteLength + pad);
	out.set(encoded);
	for (let i = 0; i < pad; i++) {
		out[encoded.byteLength + i] = 0x20;
	}
	return out;
}

function padBinChunk(bin: ArrayBuffer): Uint8Array {
	const src = new Uint8Array(bin);
	const pad = (4 - (src.byteLength % 4)) % 4;
	const out = new Uint8Array(src.byteLength + pad);
	out.set(src);
	return out;
}

/**
 * Split a GLB 2.0 file into parsed JSON and the BIN chunk (first BIN only; sufficient for typical meshes).
 */
export function splitGlb(arrayBuffer: ArrayBuffer): { json: GltfRoot; bin: ArrayBuffer | null } {
	const view = new DataView(arrayBuffer);
	if (view.byteLength < 12 || view.getUint32(0, true) !== GLB_MAGIC) {
		throw new Error("Not a binary glTF (.glb) file.");
	}
	const version = view.getUint32(4, true);
	if (version !== 2) {
		throw new Error(`Unsupported glTF version: ${version}`);
	}
	const length = view.getUint32(8, true);
	let offset = 12;
	let json: GltfRoot | null = null;
	let bin: ArrayBuffer | null = null;
	while (offset + 8 <= length && offset + 8 <= view.byteLength) {
		const chunkLength = view.getUint32(offset, true);
		const chunkType = view.getUint32(offset + 4, true);
		const dataStart = offset + 8;
		const dataEnd = dataStart + chunkLength;
		const chunkData = arrayBuffer.slice(dataStart, dataEnd);
		if (chunkType === CHUNK_JSON && json === null) {
			json = JSON.parse(new TextDecoder().decode(chunkData)) as GltfRoot;
		} else if (chunkType === CHUNK_BIN && bin === null) {
			bin = chunkData;
		}
		offset = dataEnd;
	}
	if (!json) {
		throw new Error("GLB is missing a JSON chunk.");
	}
	return { json, bin };
}

function buildGlb(json: GltfRoot, bin: ArrayBuffer | null): ArrayBuffer {
	const jsonBytes = padJsonChunk(JSON.stringify(json));
	const binBytes = bin ? padBinChunk(bin) : new Uint8Array(0);
	const totalLength = 12 + 8 + jsonBytes.byteLength + (bin ? 8 + binBytes.byteLength : 0);
	const out = new ArrayBuffer(totalLength);
	const dv = new DataView(out);
	dv.setUint32(0, GLB_MAGIC, true);
	dv.setUint32(4, 2, true);
	dv.setUint32(8, totalLength, true);
	let o = 12;
	dv.setUint32(o, jsonBytes.byteLength, true);
	dv.setUint32(o + 4, CHUNK_JSON, true);
	new Uint8Array(out, o + 8, jsonBytes.byteLength).set(jsonBytes);
	o += 8 + jsonBytes.byteLength;
	if (bin) {
		dv.setUint32(o, binBytes.byteLength, true);
		dv.setUint32(o + 4, CHUNK_BIN, true);
		new Uint8Array(out, o + 8, binBytes.byteLength).set(binBytes);
	}
	return out;
}

async function writeImageBytesToCache(slice: Uint8Array, sessionDir: Directory, baseName: string, mime?: string): Promise<string> {
	const ext = sniffImageExt(slice, mime);
	const outFile = new File(sessionDir, `${baseName}${ext}`);
	outFile.create({ overwrite: true });
	try {
		outFile.write(new Uint8Array(slice));
	} catch {
		// Some runtimes still prefer base64 path for small compatibility gaps.
		const { writeAsStringAsync, EncodingType } = await import("expo-file-system/legacy");
		await writeAsStringAsync(outFile.uri, uint8ToBase64(slice), { encoding: EncodingType.Base64 });
	}
	return outFile.uri;
}

/**
 * React Native cannot use Blob + URL.createObjectURL for embedded glTF images. This rewrites
 * `images[].bufferView` entries to `file://` URIs under the app cache, then rebuilds a GLB
 * with the same BIN chunk (geometry data unchanged).
 */
export async function embedGlbBufferViewTexturesAsCacheFiles(arrayBuffer: ArrayBuffer): Promise<ArrayBuffer> {
	const { json, bin } = splitGlb(arrayBuffer);
	if (!bin) {
		return arrayBuffer;
	}

	const jsonCopy = JSON.parse(JSON.stringify(json)) as GltfRoot;
	const images = jsonCopy.images ?? [];
	const bufferViews = jsonCopy.bufferViews ?? [];
	const binU8 = new Uint8Array(bin);

	const sessionDir = new Directory(Paths.cache, `gltf-rn-tex-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`);
	sessionDir.create({ intermediates: true });

	for (let i = 0; i < images.length; i++) {
		const img = images[i];
		if (!img || img.bufferView === undefined || img.uri !== undefined) {
			continue;
		}
		const bvIndex = img.bufferView;
		const bv = bufferViews[bvIndex];
		if (!bv || bv.byteLength === undefined) {
			continue;
		}
		const byteOffset = bv.byteOffset ?? 0;
		const end = byteOffset + bv.byteLength;
		if (end > binU8.byteLength) {
			continue;
		}
		const slice = binU8.subarray(byteOffset, end);
		const uri = await writeImageBytesToCache(slice, sessionDir, `image-${i}`, img.mimeType);
		delete img.bufferView;
		img.uri = uri;
	}

	return buildGlb(jsonCopy, bin);
}

export async function fetchGlbArrayBuffer(modelUri: string): Promise<ArrayBuffer> {
	const res = await fetch(modelUri);
	if (!res.ok) {
		throw new Error(`Failed to fetch model (${res.status}).`);
	}
	return res.arrayBuffer();
}

export function shouldRewriteGlbTexturesForPlatform(): boolean {
	return Platform.OS !== "web";
}
