/**
 * Pathverse-style spatial graph: SQLite on native, in-memory fallback on web.
 */
import * as SQLite from "expo-sqlite";
import { Platform } from "react-native";

export type PathverseNodeRow = {
	id: string;
	name: string;
	x: number;
	y: number;
	z: number;
	type: string;
};

export type PathverseEdgeRow = {
	node1_id: string;
	node2_id: string;
	distance: number;
};

const MEM_NODES: PathverseNodeRow[] = [
	{ id: "it_gate", name: "IT Main Gate", x: 36, y: 210, z: 0, type: "room" },
	{ id: "lift_1", name: "The Lift", x: 36, y: 130, z: 0, type: "corridor" },
	{ id: "it_lab_1", name: "IT Lab 1", x: 200, y: 130, z: 0, type: "room" },
	{ id: "it301", name: "IT-301 Lab", x: 220, y: 220, z: 0, type: "room" },
	{ id: "it_corr", name: "IT Corridor", x: 130, y: 220, z: 0, type: "corridor" },
	{ id: "it302", name: "IT-302 Lab", x: 130, y: 160, z: 0, type: "room" },
	{ id: "stairs3", name: "Stairs 3rd", x: 130, y: 88, z: 0, type: "stairs" },
	{ id: "cs_fac", name: "CS Faculty", x: 220, y: 88, z: 0, type: "room" },
];

const MEM_EDGES: PathverseEdgeRow[] = [
	{ node1_id: "it301", node2_id: "it_corr", distance: 90 },
	{ node1_id: "it_corr", node2_id: "it302", distance: 60 },
	{ node1_id: "it_corr", node2_id: "stairs3", distance: 132 },
	{ node1_id: "stairs3", node2_id: "cs_fac", distance: 90 },
	{ node1_id: "it_gate", node2_id: "lift_1", distance: 80 },
	{ node1_id: "lift_1", node2_id: "it_lab_1", distance: 164 },
	{ node1_id: "it_corr", node2_id: "lift_1", distance: 95 },
	{ node1_id: "it_lab_1", node2_id: "it302", distance: 76 },
];

let memSeeded = false;

function ensureMemSeed() {
	memSeeded = true;
}

function loadMem(): { nodes: PathverseNodeRow[]; edges: PathverseEdgeRow[] } {
	ensureMemSeed();
	return { nodes: [...MEM_NODES], edges: [...MEM_EDGES] };
}

function initSqliteDb(): SQLite.SQLiteDatabase {
	const db = SQLite.openDatabaseSync("pathverse_ar.db");
	db.execSync(`
		CREATE TABLE IF NOT EXISTS LocationNodes (
			id TEXT PRIMARY KEY,
			name TEXT,
			x REAL,
			y REAL,
			z REAL,
			type TEXT
		);
		CREATE TABLE IF NOT EXISTS Edges (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			node1_id TEXT,
			node2_id TEXT,
			distance REAL
		);
	`);
	return db;
}

function seedSqliteIfEmpty(db: SQLite.SQLiteDatabase) {
	const row = db.getFirstSync<{ c: number }>("SELECT COUNT(*) AS c FROM LocationNodes");
	const count = Number(row?.c ?? 0);
	if (count > 0) {
		return;
	}
	for (const r of MEM_NODES) {
		db.runSync(
			`INSERT OR IGNORE INTO LocationNodes (id, name, x, y, z, type) VALUES (?, ?, ?, ?, ?, ?)`,
			[r.id, r.name, r.x, r.y, r.z, r.type],
		);
	}
	for (const e of MEM_EDGES) {
		db.runSync(`INSERT INTO Edges (node1_id, node2_id, distance) VALUES (?, ?, ?)`, [
			e.node1_id,
			e.node2_id,
			e.distance,
		]);
	}
}

function loadSqlite(): { nodes: PathverseNodeRow[]; edges: PathverseEdgeRow[] } {
	const db = initSqliteDb();
	seedSqliteIfEmpty(db);
	const nodes = db.getAllSync<PathverseNodeRow>("SELECT id, name, x, y, z, type FROM LocationNodes");
	const edges = db.getAllSync<PathverseEdgeRow>("SELECT node1_id, node2_id, distance FROM Edges");
	return { nodes, edges };
}

export function loadPathverseGraph(): { nodes: PathverseNodeRow[]; edges: PathverseEdgeRow[] } {
	if (Platform.OS === "web") {
		return loadMem();
	}
	try {
		return loadSqlite();
	} catch {
		return loadMem();
	}
}
