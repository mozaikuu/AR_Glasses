import { useMemo, useRef } from "react";
import { PanResponder, Pressable, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

export type WalkInputState = {
	moveForward: number;
	moveStrafe: number;
	lookDx: number;
	lookDy: number;
};

export function createWalkInputState(): WalkInputState {
	return { moveForward: 0, moveStrafe: 0, lookDx: 0, lookDy: 0 };
}

type Props = {
	inputRef: React.MutableRefObject<WalkInputState>;
	onRecenter: () => void;
};

/**
 * Touch look + on-screen move controls layered above GLView (walk mode).
 */
export function GlbWalkHud({ inputRef, onRecenter }: Props) {
	const panLast = useRef({ dx: 0, dy: 0 });

	const panHandlers = useMemo(
		() =>
			PanResponder.create({
				onStartShouldSetPanResponder: () => true,
				onMoveShouldSetPanResponder: () => true,
				onPanResponderGrant: () => {
					panLast.current = { dx: 0, dy: 0 };
				},
				onPanResponderMove: (_, gs) => {
					const ddx = gs.dx - panLast.current.dx;
					const ddy = gs.dy - panLast.current.dy;
					panLast.current = { dx: gs.dx, dy: gs.dy };
					inputRef.current.lookDx += ddx;
					inputRef.current.lookDy += ddy;
				},
				onPanResponderRelease: () => {
					panLast.current = { dx: 0, dy: 0 };
				},
				onPanResponderTerminate: () => {
					panLast.current = { dx: 0, dy: 0 };
				},
			}).panHandlers,
		[inputRef],
	);

	return (
		<View style={styles.root} pointerEvents="box-none">
			<View style={styles.lookZone} {...panHandlers} />
			<View style={styles.controls} pointerEvents="box-none">
				<Pressable style={styles.recenter} onPress={onRecenter}>
					<Ionicons name="locate" size={22} color="#fff" />
					<Text style={styles.recenterTxt}>Recenter</Text>
				</Pressable>
				<View style={styles.dpad}>
					<View style={styles.padRow}>
						<View style={styles.padSpacer} />
						<MoveButton
							icon="arrow-up"
							onPressIn={() => {
								inputRef.current.moveForward += 1;
							}}
							onPressOut={() => {
								inputRef.current.moveForward -= 1;
							}}
						/>
						<View style={styles.padSpacer} />
					</View>
					<View style={styles.padRow}>
						<MoveButton
							icon="arrow-back"
							onPressIn={() => {
								inputRef.current.moveStrafe -= 1;
							}}
							onPressOut={() => {
								inputRef.current.moveStrafe += 1;
							}}
						/>
						<View style={styles.padCenter} />
						<MoveButton
							icon="arrow-forward"
							onPressIn={() => {
								inputRef.current.moveStrafe += 1;
							}}
							onPressOut={() => {
								inputRef.current.moveStrafe -= 1;
							}}
						/>
					</View>
					<View style={styles.padRow}>
						<View style={styles.padSpacer} />
						<MoveButton
							icon="arrow-down"
							onPressIn={() => {
								inputRef.current.moveForward -= 1;
							}}
							onPressOut={() => {
								inputRef.current.moveForward += 1;
							}}
						/>
						<View style={styles.padSpacer} />
					</View>
				</View>
				<Text style={styles.hint}>Drag empty area to look · D-pad moves on the ground plane</Text>
			</View>
		</View>
	);
}

function MoveButton({
	icon,
	onPressIn,
	onPressOut,
}: {
	icon: keyof typeof Ionicons.glyphMap;
	onPressIn: () => void;
	onPressOut: () => void;
}) {
	return (
		<Pressable
			style={({ pressed }) => [styles.moveBtn, pressed && styles.moveBtnPressed]}
			onPressIn={onPressIn}
			onPressOut={onPressOut}
		>
			<Ionicons name={icon} size={26} color="#e2e8f0" />
		</Pressable>
	);
}

const styles = StyleSheet.create({
	root: {
		...StyleSheet.absoluteFillObject,
	},
	lookZone: {
		position: "absolute",
		top: 0,
		left: 0,
		right: 0,
		height: "58%",
	},
	controls: {
		position: "absolute",
		right: 10,
		bottom: 10,
		left: 10,
		alignItems: "flex-end",
		gap: 10,
	},
	recenter: {
		flexDirection: "row",
		alignItems: "center",
		gap: 6,
		backgroundColor: "rgba(15,23,42,0.75)",
		paddingHorizontal: 12,
		paddingVertical: 8,
		borderRadius: 10,
	},
	recenterTxt: { color: "#fff", fontWeight: "600", fontSize: 14 },
	dpad: {
		backgroundColor: "rgba(15,23,42,0.55)",
		borderRadius: 12,
		padding: 8,
		alignItems: "center",
	},
	padRow: { flexDirection: "row", alignItems: "center", justifyContent: "center" },
	padSpacer: { width: 52, height: 52 },
	padCenter: { width: 52, height: 52 },
	moveBtn: {
		width: 52,
		height: 52,
		borderRadius: 10,
		backgroundColor: "rgba(30,41,59,0.9)",
		justifyContent: "center",
		alignItems: "center",
		margin: 4,
	},
	moveBtnPressed: { backgroundColor: "rgba(51,65,85,0.95)" },
	hint: {
		color: "#e2e8f0",
		fontSize: 11,
		maxWidth: 260,
		textAlign: "right",
		lineHeight: 14,
		textShadowColor: "rgba(0,0,0,0.6)",
		textShadowRadius: 4,
	},
});
