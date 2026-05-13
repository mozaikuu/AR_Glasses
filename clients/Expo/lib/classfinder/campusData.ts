/** Demo campus data (SOEN390-style building codes + schedule + POIs). */

export type FloorOption = { key: string; label: string };

export const FLOORS_BY_BUILDING: Record<string, FloorOption[]> = {
	H: [
		{ key: "H-1", label: "Floor 1" },
		{ key: "H-2", label: "Floor 2" },
		{ key: "H-8", label: "Floor 8" },
		{ key: "H-9", label: "Floor 9" },
	],
	MB: [
		{ key: "MB-1", label: "Floor 1" },
		{ key: "MB--2", label: "S2" },
	],
	VE: [
		{ key: "VE-1", label: "Floor 1" },
		{ key: "VE-2", label: "Floor 2" },
	],
	VL: [
		{ key: "VL-1", label: "Floor 1" },
		{ key: "VL-2", label: "Floor 2" },
	],
};

export type CampusBuilding = {
	code: keyof typeof FLOORS_BY_BUILDING | string;
	name: string;
	color: string;
	/** SVG layout in viewBox 0–320 × 0–220 */
	map: { x: number; y: number; w: number; h: number };
};

export const CAMPUS_BUILDINGS: CampusBuilding[] = [
	{ code: "H", name: "Henry (H)", color: "#2563eb", map: { x: 24, y: 48, w: 72, h: 120 } },
	{ code: "MB", name: "J.W. McConnell (MB)", color: "#7c3aed", map: { x: 118, y: 28, w: 88, h: 100 } },
	{ code: "VE", name: "Visual Collections (VE)", color: "#059669", map: { x: 118, y: 142, w: 88, h: 68 } },
	{ code: "VL", name: "Vanier Lib. (VL)", color: "#ea580c", map: { x: 228, y: 72, w: 76, h: 108 } },
];

export type LectureDemo = {
	id: string;
	title: string;
	courseCode: string;
	roomRaw: string;
	day: string;
	start: string;
	end: string;
};

export const DEMO_LECTURES: LectureDemo[] = [
	{
		id: "1",
		title: "Software Engineering Design",
		courseCode: "SOEN 390",
		roomRaw: "H 920",
		day: "Thu",
		start: "10:15",
		end: "13:30",
	},
	{
		id: "2",
		title: "User Interface Design",
		courseCode: "SOEN 357",
		roomRaw: "MB-S2",
		day: "Thu",
		start: "14:45",
		end: "17:30",
	},
	{
		id: "3",
		title: "Computer Vision",
		courseCode: "COMP 425",
		roomRaw: "VE-201",
		day: "Thu",
		start: "18:00",
		end: "20:30",
	},
];

export type PoiDemo = {
	id: string;
	name: string;
	category: "washroom" | "food" | "study" | "transit";
	building: string;
	floorKey: string;
};

export const DEMO_POIS: PoiDemo[] = [
	{ id: "w1", name: "Washroom — H-2 east", category: "washroom", building: "H", floorKey: "H-2" },
	{ id: "w2", name: "Washroom — MB-1", category: "washroom", building: "MB", floorKey: "MB-1" },
	{ id: "f1", name: "Tim’s — MB tunnel", category: "food", building: "MB", floorKey: "MB-1" },
	{ id: "f2", name: "Food court — H-2", category: "food", building: "H", floorKey: "H-2" },
	{ id: "s1", name: "Silent study — VL-2", category: "study", building: "VL", floorKey: "VL-2" },
	{ id: "t1", name: "Shuttle stop — MB exit", category: "transit", building: "MB", floorKey: "MB-1" },
];
