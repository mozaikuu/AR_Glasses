import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import {
	addGraphEdge,
	addGraphNode,
	addLocation,
	deleteGraphEdge,
	deleteGraphNode,
	deleteLocation,
	ensureFloorMeta,
	updateGraphNode,
	updateLocation,
} from "@/lib/indoor-nav/editor";
import { formatRoomCode, idFromRoomCode, parseRoomCode } from "@/lib/indoor-nav/roomCodes";
import type { GraphNode, IndoorBuildingV1, IndoorLocation, MapPlaceKind } from "@/lib/indoor-nav/types";

const MAP_KINDS: MapPlaceKind[] = [
	"room",
	"stairs",
	"bathroom",
	"elevator",
	"office",
	"lecture_room",
	"lab",
	"corridor",
	"service",
	"garden",
	"storage",
	"general",
];

export type EditorSelection =
	| { kind: "location"; id: string }
	| { kind: "node"; id: string }
	| { kind: "edge"; id: string }
	| null;

type Props = {
	building: IndoorBuildingV1;
	setBuilding: (b: IndoorBuildingV1) => void;
	viewedFloor: number;
	setViewedFloor: (f: number) => void;
	selection: EditorSelection;
	setSelection: (s: EditorSelection) => void;
	onPersist: () => Promise<void>;
	setStatusMsg: (msg: string | null) => void;
};

export function EditorPanel(props: Props) {
	const { building, setBuilding, viewedFloor, setViewedFloor, selection, setSelection, onPersist, setStatusMsg } =
		props;

	const nodesOnFloor = useMemo(
		() => building.graph.nodes.filter((n) => n.floor === viewedFloor),
		[building.graph.nodes, viewedFloor],
	);
	const locsOnFloor = useMemo(
		() => building.locations.filter((l) => l.floor === viewedFloor),
		[building.locations, viewedFloor],
	);
	const edgesOnFloor = useMemo(() => {
		const byId = new Map(building.graph.nodes.map((n) => [n.id, n]));
		return building.graph.edges.filter((e) => {
			const a = byId.get(e.from);
			const b = byId.get(e.to);
			return a && b && a.floor === viewedFloor && b.floor === viewedFloor;
		});
	}, [building.graph, viewedFloor]);

	const [draftLoc, setDraftLoc] = useState<Partial<IndoorLocation>>({});
	const [draftNode, setDraftNode] = useState<Partial<GraphNode>>({});
	const [draftEdgeFrom, setDraftEdgeFrom] = useState("");
	const [draftEdgeTo, setDraftEdgeTo] = useState("");
	const [roomCodeInput, setRoomCodeInput] = useState("");

	const selectedLoc = useMemo(
		() => (selection?.kind === "location" ? building.locations.find((l) => l.id === selection.id) : null),
		[building.locations, selection],
	);
	const selectedNode = useMemo(
		() => (selection?.kind === "node" ? building.graph.nodes.find((n) => n.id === selection.id) : null),
		[building.graph.nodes, selection],
	);
	const selectedEdge = useMemo(
		() => (selection?.kind === "edge" ? building.graph.edges.find((e) => e.id === selection.id) : null),
		[building.graph.edges, selection],
	);

	useEffect(() => {
		if (selectedLoc) {
			setDraftLoc({ ...selectedLoc });
			setRoomCodeInput(selectedLoc.roomCode ?? "");
		} else {
			setDraftLoc({});
			setRoomCodeInput("");
		}
	}, [selectedLoc]);

	useEffect(() => {
		if (selectedNode) {
			setDraftNode({ ...selectedNode });
		} else {
			setDraftNode({});
		}
	}, [selectedNode]);

	useEffect(() => {
		if (selectedEdge) {
			setDraftEdgeFrom(selectedEdge.from);
			setDraftEdgeTo(selectedEdge.to);
		} else {
			setDraftEdgeFrom("");
			setDraftEdgeTo("");
		}
	}, [selectedEdge]);

	const applyLocationPatch = useCallback(() => {
		if (!selection || selection.kind !== "location") {
			return;
		}
		const id = selection.id;
		const patch: Partial<IndoorLocation> = {
			name: draftLoc.name ?? "",
			floor: typeof draftLoc.floor === "number" ? draftLoc.floor : viewedFloor,
			coordinates: {
				x: Number(draftLoc.coordinates?.x) || 0,
				y: Number(draftLoc.coordinates?.y) || 0,
			},
			description: draftLoc.description,
			additional_info: draftLoc.additional_info,
			mapKind: draftLoc.mapKind,
			shortLabel: draftLoc.shortLabel,
			buildingId: draftLoc.buildingId,
			roomCode: roomCodeInput.trim() || undefined,
			nearestNodeId: draftLoc.nearestNodeId || undefined,
			proximityRadius: draftLoc.proximityRadius != null ? Number(draftLoc.proximityRadius) : undefined,
			isNavObstacle: draftLoc.isNavObstacle,
			size:
				draftLoc.size && draftLoc.size.width > 0 && draftLoc.size.height > 0
					? { width: Number(draftLoc.size.width), height: Number(draftLoc.size.height) }
					: undefined,
		};
		setBuilding(updateLocation(building, id, patch));
		setStatusMsg("Location updated (tap Save map to persist).");
	}, [building, draftLoc, roomCodeInput, selection, setBuilding, setStatusMsg, viewedFloor]);

	const applyNodePatch = useCallback(() => {
		if (!selection || selection.kind !== "node") {
			return;
		}
		const id = selection.id;
		setBuilding(
			updateGraphNode(building, id, {
				label: draftNode.label,
				floor: typeof draftNode.floor === "number" ? draftNode.floor : viewedFloor,
				position: {
					x: Number(draftNode.position?.x) || 0,
					y: Number(draftNode.position?.y) || 0,
				},
				qrPayload: draftNode.qrPayload,
			}),
		);
		setStatusMsg("Node updated.");
	}, [building, draftNode, selection, setBuilding, setStatusMsg, viewedFloor]);

	const applyEdgePatch = useCallback(() => {
		if (!selection || selection.kind !== "edge") {
			return;
		}
		const id = selection.id;
		setBuilding({
			...building,
			graph: {
				nodes: building.graph.nodes,
				edges: building.graph.edges.map((e) =>
					e.id === id ? { ...e, from: draftEdgeFrom.trim(), to: draftEdgeTo.trim() } : e,
				),
			},
		});
		setStatusMsg("Edge updated.");
	}, [building, draftEdgeFrom, draftEdgeTo, selection, setBuilding, setStatusMsg]);

	const addBlankLocation = useCallback(() => {
		const nid = `loc_${Date.now()}`;
		const loc: IndoorLocation = {
			id: nid,
			name: "New place",
			floor: viewedFloor,
			coordinates: { x: 20, y: 20 },
			mapKind: "room",
			shortLabel: "?",
			proximityRadius: 2,
		};
		setBuilding(ensureFloorMeta(addLocation(building, loc), viewedFloor));
		setSelection({ kind: "location", id: nid });
		setStatusMsg("Added location.");
	}, [building, setBuilding, setSelection, setStatusMsg, viewedFloor]);

	const addBlankNode = useCallback(() => {
		const b2 = ensureFloorMeta(building, viewedFloor);
		const updated = addGraphNode(b2, {
			floor: viewedFloor,
			position: { x: 30, y: 30 },
			label: "Checkpoint",
		});
		const added = updated.graph.nodes[updated.graph.nodes.length - 1];
		setBuilding(updated);
		setSelection({ kind: "node", id: added.id });
		setStatusMsg("Added node.");
	}, [building, setBuilding, setSelection, setStatusMsg, viewedFloor]);

	const addBlankEdge = useCallback(() => {
		const nodes = nodesOnFloor;
		if (nodes.length < 2) {
			setStatusMsg("Need at least two nodes on this floor to add an edge.");
			return;
		}
		const b2 = addGraphEdge(building, nodes[0].id, nodes[1].id);
		const added = b2.graph.edges[b2.graph.edges.length - 1];
		setBuilding(b2);
		setSelection({ kind: "edge", id: added.id });
		setStatusMsg("Added edge between first two nodes on floor (edit endpoints).");
	}, [building, nodesOnFloor, setBuilding, setSelection, setStatusMsg]);

	const deleteSelected = useCallback(() => {
		if (!selection) {
			return;
		}
		if (selection.kind === "location") {
			setBuilding(deleteLocation(building, selection.id));
		} else if (selection.kind === "node") {
			setBuilding(deleteGraphNode(building, selection.id));
		} else {
			setBuilding(deleteGraphEdge(building, selection.id));
		}
		setSelection(null);
		setStatusMsg("Deleted.");
	}, [building, selection, setBuilding, setSelection, setStatusMsg]);

	const applyRoomCode = useCallback(() => {
		const code = roomCodeInput.trim();
		if (!code) {
			return;
		}
		const parsed = parseRoomCode(code);
		if (!parsed) {
			setStatusMsg("Room code must look like 2-1-46");
			return;
		}
		const newId = idFromRoomCode(code);
		if (selection?.kind !== "location") {
			return;
		}
		const loc = building.locations.find((l) => l.id === selection.id);
		if (!loc) {
			return;
		}
		if (newId !== loc.id && building.locations.some((l) => l.id === newId)) {
			setStatusMsg(`Id ${newId} already exists.`);
			return;
		}
		const updated: IndoorLocation = {
			...loc,
			id: newId,
			roomCode: formatRoomCode(parsed.buildingId, parsed.floor, parsed.room),
			buildingId: parsed.buildingId,
			floor: parsed.floor,
		};
		setBuilding({
			...building,
			locations: building.locations.map((l) => (l.id === loc.id ? updated : l)),
		});
		setSelection({ kind: "location", id: newId });
		setStatusMsg("Applied room code to id and fields.");
	}, [building, roomCodeInput, selection, setBuilding, setSelection, setStatusMsg]);

	return (
		<ScrollView style={styles.wrap} contentContainerStyle={styles.inner}>
			<Text style={styles.title}>Map editor</Text>
			<Text style={styles.hint}>Edit on floor {viewedFloor}. Use Save map in settings to persist.</Text>

			<View style={styles.row}>
				<Text style={styles.lbl}>Edit floor</Text>
				<TextInput
					value={String(viewedFloor)}
					onChangeText={(t) => {
						const n = Number.parseInt(t, 10);
						if (Number.isFinite(n)) {
							setViewedFloor(n);
						}
					}}
					keyboardType="number-pad"
					style={styles.inpSm}
				/>
			</View>

			<Text style={styles.section}>Pick</Text>
			<Text style={styles.sub}>Locations on this floor</Text>
			{locsOnFloor.map((l) => (
				<Pressable
					key={l.id}
					style={[styles.pick, selection?.kind === "location" && selection.id === l.id && styles.pickOn]}
					onPress={() => setSelection({ kind: "location", id: l.id })}
				>
					<Text style={styles.pickTxt}>{l.shortLabel ?? l.name}</Text>
					<Text style={styles.pickMeta}>{l.id}</Text>
				</Pressable>
			))}
			<Text style={styles.sub}>Nodes</Text>
			{nodesOnFloor.map((n) => (
				<Pressable
					key={n.id}
					style={[styles.pick, selection?.kind === "node" && selection.id === n.id && styles.pickOn]}
					onPress={() => setSelection({ kind: "node", id: n.id })}
				>
					<Text style={styles.pickTxt}>{n.label ?? n.id}</Text>
					<Text style={styles.pickMeta}>{n.id}</Text>
				</Pressable>
			))}
			<Text style={styles.sub}>Edges (same floor)</Text>
			{edgesOnFloor.map((e) => (
				<Pressable
					key={e.id}
					style={[styles.pick, selection?.kind === "edge" && selection.id === e.id && styles.pickOn]}
					onPress={() => setSelection({ kind: "edge", id: e.id })}
				>
					<Text style={styles.pickTxt}>
						{e.from} → {e.to}
					</Text>
					<Text style={styles.pickMeta}>{e.id}</Text>
				</Pressable>
			))}

			<View style={styles.btnRow}>
				<Pressable style={styles.btn} onPress={addBlankLocation}>
					<Text style={styles.btnTxt}>+ Location</Text>
				</Pressable>
				<Pressable style={styles.btn} onPress={addBlankNode}>
					<Text style={styles.btnTxt}>+ Node</Text>
				</Pressable>
				<Pressable style={styles.btn} onPress={addBlankEdge}>
					<Text style={styles.btnTxt}>+ Edge</Text>
				</Pressable>
			</View>

			{selection?.kind === "location" && selectedLoc && (
				<View style={styles.form}>
					<Text style={styles.section}>Edit location</Text>
					<Text style={styles.lbl}>Id</Text>
					<Text style={styles.read}>{selectedLoc.id}</Text>
					<Text style={styles.lbl}>Name</Text>
					<TextInput style={styles.inp} value={draftLoc.name ?? ""} onChangeText={(t) => setDraftLoc((d) => ({ ...d, name: t }))} />
					<Text style={styles.lbl}>Short map label (e.g. 46, S, B)</Text>
					<TextInput
						style={styles.inp}
						value={draftLoc.shortLabel ?? ""}
						onChangeText={(t) => setDraftLoc((d) => ({ ...d, shortLabel: t }))}
					/>
					<Text style={styles.lbl}>Room code (2-1-46)</Text>
					<TextInput style={styles.inp} value={roomCodeInput} onChangeText={setRoomCodeInput} autoCapitalize="none" />
					<Pressable style={styles.btnSec} onPress={applyRoomCode}>
						<Text style={styles.btnSecTxt}>Apply code to id</Text>
					</Pressable>
					<Text style={styles.lbl}>Kind</Text>
					<ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginVertical: 6 }}>
						{MAP_KINDS.map((k) => (
							<Pressable
								key={k}
								style={[styles.chip, draftLoc.mapKind === k && styles.chipOn]}
								onPress={() => setDraftLoc((d) => ({ ...d, mapKind: k }))}
							>
								<Text style={[styles.chipTxt, draftLoc.mapKind === k && styles.chipTxtOn]}>{k}</Text>
							</Pressable>
						))}
					</ScrollView>
					<Text style={styles.lbl}>X / Y / W / H</Text>
					<View style={styles.row4}>
						<TextInput
							style={styles.inpSm}
							keyboardType="decimal-pad"
							value={String(draftLoc.coordinates?.x ?? 0)}
							onChangeText={(t) =>
								setDraftLoc((d) => ({
									...d,
									coordinates: { x: Number(t) || 0, y: d.coordinates?.y ?? 0 },
								}))
							}
						/>
						<TextInput
							style={styles.inpSm}
							keyboardType="decimal-pad"
							value={String(draftLoc.coordinates?.y ?? 0)}
							onChangeText={(t) =>
								setDraftLoc((d) => ({
									...d,
									coordinates: { x: d.coordinates?.x ?? 0, y: Number(t) || 0 },
								}))
							}
						/>
						<TextInput
							style={styles.inpSm}
							keyboardType="decimal-pad"
							placeholder="w"
							value={draftLoc.size?.width != null ? String(draftLoc.size.width) : ""}
							onChangeText={(t) =>
								setDraftLoc((d) => ({
									...d,
									size: { width: Number(t) || 0, height: d.size?.height ?? 0 },
								}))
							}
						/>
						<TextInput
							style={styles.inpSm}
							keyboardType="decimal-pad"
							placeholder="h"
							value={draftLoc.size?.height != null ? String(draftLoc.size.height) : ""}
							onChangeText={(t) =>
								setDraftLoc((d) => ({
									...d,
									size: { width: d.size?.width ?? 0, height: Number(t) || 0 },
								}))
							}
						/>
					</View>
					<Text style={styles.lbl}>Proximity radius</Text>
					<TextInput
						style={styles.inp}
						keyboardType="decimal-pad"
						value={draftLoc.proximityRadius != null ? String(draftLoc.proximityRadius) : ""}
						onChangeText={(t) => setDraftLoc((d) => ({ ...d, proximityRadius: Number(t) || 0 }))}
					/>
					<Text style={styles.lbl}>Nearest graph node id</Text>
					<TextInput
						style={styles.inp}
						value={draftLoc.nearestNodeId ?? ""}
						onChangeText={(t) => setDraftLoc((d) => ({ ...d, nearestNodeId: t || undefined }))}
						autoCapitalize="none"
					/>
					<Text style={styles.lbl}>Nav obstacle (hide from destination list)</Text>
					<Pressable
						style={[styles.chip, draftLoc.isNavObstacle && styles.chipOn]}
						onPress={() => setDraftLoc((d) => ({ ...d, isNavObstacle: !d.isNavObstacle }))}
					>
						<Text style={[styles.chipTxt, draftLoc.isNavObstacle && styles.chipTxtOn]}>
							{draftLoc.isNavObstacle ? "Yes" : "No"}
						</Text>
					</Pressable>
					<Pressable style={styles.btn} onPress={applyLocationPatch}>
						<Text style={styles.btnTxt}>Apply location</Text>
					</Pressable>
				</View>
			)}

			{selection?.kind === "node" && selectedNode && (
				<View style={styles.form}>
					<Text style={styles.section}>Edit node</Text>
					<Text style={styles.lbl}>Id</Text>
					<Text style={styles.read}>{selectedNode.id}</Text>
					<Text style={styles.lbl}>Label</Text>
					<TextInput style={styles.inp} value={draftNode.label ?? ""} onChangeText={(t) => setDraftNode((d) => ({ ...d, label: t }))} />
					<Text style={styles.lbl}>QR payload</Text>
					<TextInput
						style={styles.inp}
						value={draftNode.qrPayload ?? ""}
						onChangeText={(t) => setDraftNode((d) => ({ ...d, qrPayload: t }))}
						autoCapitalize="none"
					/>
					<Text style={styles.lbl}>X / Y</Text>
					<View style={styles.row4}>
						<TextInput
							style={styles.inpSm}
							keyboardType="decimal-pad"
							value={String(draftNode.position?.x ?? 0)}
							onChangeText={(t) =>
								setDraftNode((d) => ({
									...d,
									position: { x: Number(t) || 0, y: d.position?.y ?? 0 },
								}))
							}
						/>
						<TextInput
							style={styles.inpSm}
							keyboardType="decimal-pad"
							value={String(draftNode.position?.y ?? 0)}
							onChangeText={(t) =>
								setDraftNode((d) => ({
									...d,
									position: { x: d.position?.x ?? 0, y: Number(t) || 0 },
								}))
							}
						/>
					</View>
					<Pressable style={styles.btn} onPress={applyNodePatch}>
						<Text style={styles.btnTxt}>Apply node</Text>
					</Pressable>
				</View>
			)}

			{selection?.kind === "edge" && selectedEdge && (
				<View style={styles.form}>
					<Text style={styles.section}>Edit edge</Text>
					<Text style={styles.lbl}>From node id</Text>
					<TextInput style={styles.inp} value={draftEdgeFrom} onChangeText={setDraftEdgeFrom} autoCapitalize="none" />
					<Text style={styles.lbl}>To node id</Text>
					<TextInput style={styles.inp} value={draftEdgeTo} onChangeText={setDraftEdgeTo} autoCapitalize="none" />
					<Pressable style={styles.btn} onPress={applyEdgePatch}>
						<Text style={styles.btnTxt}>Apply edge</Text>
					</Pressable>
				</View>
			)}

			<View style={styles.btnRow}>
				<Pressable style={styles.danger} onPress={deleteSelected}>
					<Text style={styles.btnTxt}>Delete selected</Text>
				</Pressable>
				<Pressable style={styles.btn} onPress={() => void onPersist()}>
					<Text style={styles.btnTxt}>Save map now</Text>
				</Pressable>
			</View>
		</ScrollView>
	);
}

const styles = StyleSheet.create({
	wrap: { maxHeight: 420, marginTop: 8 },
	inner: { paddingBottom: 24 },
	title: { fontSize: 17, fontWeight: "800", color: "#0f172a" },
	hint: { color: "#64748b", fontSize: 12, marginTop: 4 },
	section: { marginTop: 14, fontWeight: "700", color: "#0f172a" },
	sub: { marginTop: 8, fontSize: 12, fontWeight: "600", color: "#475569" },
	pick: { paddingVertical: 8, paddingHorizontal: 10, borderRadius: 8, backgroundColor: "#f1f5f9", marginTop: 4 },
	pickOn: { backgroundColor: "#dbeafe" },
	pickTxt: { fontWeight: "600", color: "#0f172a" },
	pickMeta: { fontSize: 11, color: "#64748b" },
	row: { flexDirection: "row", alignItems: "center", gap: 8, marginTop: 8 },
	row4: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
	lbl: { marginTop: 8, fontSize: 12, fontWeight: "600", color: "#334155" },
	read: { fontSize: 12, color: "#64748b" },
	inp: {
		borderWidth: 1,
		borderColor: "#cbd5e1",
		borderRadius: 8,
		padding: 10,
		marginTop: 4,
		fontSize: 15,
	},
	inpSm: {
		borderWidth: 1,
		borderColor: "#cbd5e1",
		borderRadius: 8,
		padding: 8,
		width: 72,
		marginTop: 4,
		fontSize: 14,
	},
	form: { marginTop: 8 },
	btnRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 12 },
	btn: { backgroundColor: "#2563eb", paddingVertical: 10, paddingHorizontal: 14, borderRadius: 10 },
	btnTxt: { color: "#fff", fontWeight: "700", fontSize: 13 },
	btnSec: { marginTop: 8, alignSelf: "flex-start", paddingVertical: 8, paddingHorizontal: 12, borderRadius: 8, borderWidth: 1, borderColor: "#94a3b8" },
	btnSecTxt: { color: "#0f172a", fontWeight: "600", fontSize: 13 },
	danger: { backgroundColor: "#dc2626", paddingVertical: 10, paddingHorizontal: 14, borderRadius: 10 },
	chip: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 16, backgroundColor: "#e2e8f0", marginRight: 6 },
	chipOn: { backgroundColor: "#2563eb" },
	chipTxt: { fontSize: 11, color: "#334155", fontWeight: "600" },
	chipTxtOn: { color: "#fff" },
});
