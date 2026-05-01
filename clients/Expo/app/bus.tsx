import React, { useState, useEffect, useRef, useCallback } from "react";
import {
	View,
	Text,
	TouchableOpacity,
	StyleSheet,
	Dimensions,
	Alert,
	TextInput,
} from "react-native";
import { WebView } from "react-native-webview";

const { width, height } = Dimensions.get("window");

// Default region (Cairo, Egypt)
const INITIAL_CENTER = {
	latitude: 30.0444,
	longitude: 31.2357,
	zoom: 13,
};

type Position = {
	latitude: number;
	longitude: number;
};

type TrackingStatus = "idle" | "tracking" | "stopped";

export default function Bus() {
	// Path setup state
	const [startPos, setStartPos] = useState<Position | null>(null);
	const [endPos, setEndPos] = useState<Position | null>(null);
	const [isEditingPath, setIsEditingPath] = useState(true);
	const [mapClickPos, setMapClickPos] = useState<Position | null>(null);

	// Time state - simple string format "HH:MM"
	const [startTime, setStartTime] = useState("7:00");
	const [endTime, setEndTime] = useState("8:20");

	// Tracking state
	const [trackingStatus, setTrackingStatus] = useState<TrackingStatus>("idle");
	const [currentPos, setCurrentPos] = useState<Position | null>(null);
	const [progress, setProgress] = useState(0); // 0-1 along route
	const [speed, setSpeed] = useState(0); // km/h
	const [distanceRemaining, setDistanceRemaining] = useState(0); // km
	const [eta, setEta] = useState("");
	const [statusMessage, setStatusMessage] = useState("Set your route");

	// Route state
	const [generatedRoute, setGeneratedRoute] = useState<Position[]>([]);

	// Stop simulation
	const [isStopped, setIsStopped] = useState(false);
	const [stopReason, setStopReason] = useState("");
	const [stopTimer, setStopTimer] = useState(0);

	// Refs
	const webViewRef = useRef<WebView>(null);
	const trackingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(
		null,
	);
	const mapInitialized = useRef(false);

	// Generate a simple route between two points (interpolated line with some curve)
	const generateRoute = (start: Position, end: Position): Position[] => {
		const points: Position[] = [];
		const steps = 50; // Number of points in the route

		// Add some randomness to make it look like a real road
		const randomOffset = (Math.random() - 0.5) * 0.01;

		for (let i = 0; i <= steps; i++) {
			const t = i / steps;
			// Simple interpolation with a slight curve
			const lat = start.latitude + (end.latitude - start.latitude) * t;
			const lng = start.longitude + (end.longitude - start.longitude) * t;

			// Add curve effect in the middle
			const curveFactor = Math.sin(t * Math.PI) * randomOffset;
			points.push({
				latitude: lat + curveFactor,
				longitude: lng + curveFactor,
			});
		}

		return points;
	};

	// Calculate distance between two points (Haversine formula)
	const calculateDistance = (pos1: Position, pos2: Position): number => {
		const R = 6371; // Earth's radius in km
		const dLat = ((pos2.latitude - pos1.latitude) * Math.PI) / 180;
		const dLng = ((pos2.longitude - pos1.longitude) * Math.PI) / 180;
		const a =
			Math.sin(dLat / 2) * Math.sin(dLat / 2) +
			Math.cos((pos1.latitude * Math.PI) / 180) *
				Math.cos((pos2.latitude * Math.PI) / 180) *
				Math.sin(dLng / 2) *
				Math.sin(dLng / 2);
		const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
		return R * c;
	};

	// Handle map click - receive position from WebView
	const handleWebViewMessage = useCallback(
		(event: any) => {
			try {
				const data = JSON.parse(event.nativeEvent.data);
				if (data.type === "mapClick" && isEditingPath) {
					setMapClickPos(data.position);
				}
			} catch (e) {
				console.log("Error parsing WebView message:", e);
			}
		},
		[isEditingPath],
	);

	// Process map click to set start/end positions
	useEffect(() => {
		if (mapClickPos && isEditingPath && trackingStatus !== "tracking") {
			if (!startPos) {
				setStartPos(mapClickPos);
				setStatusMessage("Now select the end position");
			} else if (!endPos) {
				setEndPos(mapClickPos);
				setStatusMessage("Route set! Press 'Start Tracking' to begin");
				// Generate the route
				const route = generateRoute(startPos, mapClickPos);
				setGeneratedRoute(route);
			} else {
				// Reset and start over
				setStartPos(mapClickPos);
				setEndPos(null);
				setGeneratedRoute([]);
				setStatusMessage(
					"Start position updated. Now select the end position",
				);
			}
			setMapClickPos(null);
		}
	}, [mapClickPos, isEditingPath, trackingStatus, startPos, endPos]);

	// Send commands to WebView
	const sendToWebView = useCallback((data: any) => {
		if (webViewRef.current) {
			webViewRef.current.postMessage(JSON.stringify(data));
		}
	}, []);

	// Update map markers and route
	useEffect(() => {
		if (mapInitialized.current) {
			sendToWebView({
				type: "updateMap",
				startPos,
				endPos,
				currentPos,
				route: generatedRoute,
				center: startPos || endPos || INITIAL_CENTER,
			});
		}
	}, [startPos, endPos, currentPos, generatedRoute, sendToWebView]);

	// Start tracking
	const startTracking = () => {
		if (!startPos || !endPos || generatedRoute.length === 0) {
			Alert.alert("Error", "Please set both start and end positions first");
			return;
		}

		setIsEditingPath(false);
		setTrackingStatus("tracking");
		setProgress(0);
		setCurrentPos(startPos);
		setIsStopped(false);
		setStopReason("");

		// Calculate total distance
		let totalDistance = 0;
		for (let i = 1; i < generatedRoute.length; i++) {
			totalDistance += calculateDistance(
				generatedRoute[i - 1],
				generatedRoute[i],
			);
		}
		setDistanceRemaining(totalDistance);

		// Calculate ETA from start time to end time
		const [startHour, startMin] = startTime.split(":").map(Number);
		const [endHour, endMin] = endTime.split(":").map(Number);
		const startMinutes = startHour * 60 + startMin;
		const endMinutes = endHour * 60 + endMin;
		const durationMinutes = endMinutes - startMinutes;
		setEta(`${durationMinutes} min`);

		setStatusMessage("Tracking started");
		setSpeed(30);

		// Start tracking interval
		trackingIntervalRef.current = setInterval(() => {
			if (isStopped) {
				// Count down stop timer
				setStopTimer((prev) => {
					if (prev <= 1) {
						setIsStopped(false);
						setStopReason("");
						return 0;
					}
					return prev - 1;
				});
				return;
			}

			// Move along the route
			setProgress((prev) => {
				const increment = 0.005 + Math.random() * 0.005; // Variable speed
				const newProgress = prev + increment;

				if (newProgress >= 1) {
					// Reached destination
					stopTracking("Destination reached!");
					return 1;
				}

				// Update current position
				const routeIndex = Math.floor(
					newProgress * (generatedRoute.length - 1),
				);
				const currentRoutePos = generatedRoute[routeIndex];
				setCurrentPos(currentRoutePos);

				// Update speed with some variation
				const newSpeed = 20 + Math.random() * 30; // 20-50 km/h
				setSpeed(Math.round(newSpeed));

				// Update distance remaining
				let remaining = 0;
				for (let i = routeIndex; i < generatedRoute.length - 1; i++) {
					remaining += calculateDistance(
						generatedRoute[i],
						generatedRoute[i + 1],
					);
				}
				setDistanceRemaining(Math.round(remaining * 100) / 100);

				// Random stop simulation (5% chance per tick)
				if (
					Math.random() < 0.05 &&
					newProgress > 0.1 &&
					newProgress < 0.9
				) {
					triggerRandomStop(newProgress);
				}

				return newProgress;
			});
		}, 500); // Update every 500ms
	};

	// Trigger a random stop
	const triggerRandomStop = (position: number) => {
		const reasons = [
			"Traffic light",
			"Bus stop",
			"Traffic jam",
			"Passenger boarding",
		];
		const reason = reasons[Math.floor(Math.random() * reasons.length)];
		const duration = 3 + Math.floor(Math.random() * 5); // 3-8 seconds

		setIsStopped(true);
		setStopReason(reason);
		setStopTimer(duration);
		setSpeed(0);
		setStatusMessage(`Stopped: ${reason}`);
	};

	// Stop tracking
	const stopTracking = (message: string = "Tracking stopped") => {
		if (trackingIntervalRef.current) {
			clearInterval(trackingIntervalRef.current);
			trackingIntervalRef.current = null;
		}
		setTrackingStatus("stopped");
		setSpeed(0);
		setStatusMessage(message);
	};

	// Edit path (stop tracking and allow editing)
	const editPath = () => {
		stopTracking();
		setIsEditingPath(true);
		setStartPos(null);
		setEndPos(null);
		setGeneratedRoute([]);
		setProgress(0);
		setCurrentPos(null);
		setStatusMessage("Tap map to set start position");
		setIsStopped(false);
		setStopReason("");
	};

	// Cleanup on unmount
	useEffect(() => {
		return () => {
			if (trackingIntervalRef.current) {
				clearInterval(trackingIntervalRef.current);
			}
		};
	}, []);

	// Update status message based on state
	useEffect(() => {
		if (trackingStatus === "tracking" && !isStopped) {
			setStatusMessage(`Moving at ${speed} km/h`);
		}
	}, [trackingStatus, isStopped, speed]);

	// HTML for the map with Leaflet and OpenStreetMap
	const mapHtml = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { overflow: hidden; }
        #map { width: 100%; height: 100vh; position: absolute; top: 0; left: 0; right: 0; bottom: 0; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        let map = null;
        let markers = {};
        let polyline = null;

        // Initialize map immediately
        function initMap(center) {
            if (map) return;
            
            map = L.map('map', {
                zoomControl: true,
                attributionControl: false
            }).setView([center.latitude, center.longitude], center.zoom || 13);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19
            }).addTo(map);

            map.on('click', function(e) {
                if (window.ReactNativeWebView) {
                    window.ReactNativeWebView.postMessage(JSON.stringify({
                        type: 'mapClick',
                        position: { 
                            latitude: e.latlng.lat, 
                            longitude: e.latlng.lng 
                        }
                    }));
                }
            });

            // Notify that map is ready
            if (window.ReactNativeWebView) {
                window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'mapReady' }));
            }
        }

        // Create custom marker icon
        function createMarkerIcon(color, label) {
            return L.divIcon({
                html: '<div style="background:' + color + ';width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;font-size:13px;border:2px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3);">' + label + '</div>',
                className: 'custom-marker',
                iconSize: [28, 28],
                iconAnchor: [14, 14]
            });
        }

        // Update map with new data
        function updateMap(data) {
            if (!map) {
                initMap(data.center || { latitude: 30.0444, longitude: 31.2357, zoom: 13 });
            }

            // Clear existing markers
            Object.keys(markers).forEach(key => {
                if (markers[key]) {
                    map.removeLayer(markers[key]);
                }
            });
            markers = {};

            // Clear existing polyline
            if (polyline) {
                map.removeLayer(polyline);
                polyline = null;
            }

            // Add start marker
            if (data.startPos) {
                markers.start = L.marker([data.startPos.latitude, data.startPos.longitude], {
                    icon: createMarkerIcon('#34C759', 'S')
                }).addTo(map);
            }

            // Add end marker
            if (data.endPos) {
                markers.end = L.marker([data.endPos.latitude, data.endPos.longitude], {
                    icon: createMarkerIcon('#FF3B30', 'E')
                }).addTo(map);
            }

            // Add current position marker (bus)
            if (data.currentPos) {
                markers.current = L.marker([data.currentPos.latitude, data.currentPos.longitude], {
                    icon: createMarkerIcon('#007AFF', '🚌')
                }).addTo(map);
            }

            // Add route polyline
            if (data.route && data.route.length > 0) {
                const routePoints = data.route.map(p => [p.latitude, p.longitude]);
                polyline = L.polyline(routePoints, { 
                    color: '#007AFF', 
                    weight: 4,
                    opacity: 0.8
                }).addTo(map);
            }

            // Pan to show all markers
            if (data.startPos && data.endPos) {
                const bounds = L.latLngBounds([
                    [data.startPos.latitude, data.startPos.longitude],
                    [data.endPos.latitude, data.endPos.longitude]
                ]);
                map.fitBounds(bounds, { padding: [50, 50] });
            } else {
                map.setView([data.center.latitude, data.center.longitude], data.center.zoom || 13);
            }
        }

        // Listen for messages from React Native
        document.addEventListener('message', function(e) {
            try {
                const data = JSON.parse(e.data);
                if (data.type === 'updateMap') {
                    updateMap(data);
                }
            } catch (err) {
                console.error('Error parsing message:', err);
            }
        });
    </script>
</body>
</html>
	`;

	return (
		<View style={styles.container}>
			{/* Header */}
			<View style={styles.header}>
				<Text style={styles.headerTitle}>Bus Tracking</Text>
				{!isEditingPath && (
					<TouchableOpacity style={styles.editButton} onPress={editPath}>
						<Text style={styles.editButtonText}>Edit Path</Text>
					</TouchableOpacity>
				)}
			</View>

			{/* Map (WebView with Leaflet) */}
			<View style={styles.mapContainer}>
				<WebView
					ref={webViewRef}
					originWhitelist={["*"]}
					source={{ html: mapHtml }}
					style={styles.map}
					onMessage={handleWebViewMessage}
					javaScriptEnabled={true}
					domStorageEnabled={true}
					onLoad={() => {
						mapInitialized.current = true;
					}}
				/>
			</View>

			{/* Bottom Panel */}
			<View style={styles.bottomPanel}>
				{/* Status Message */}
				<View style={styles.statusContainer}>
					<Text style={styles.statusMessage}>{statusMessage}</Text>
					{isStopped && (
						<Text style={styles.stopTimer}>
							Resuming in {stopTimer}s...
						</Text>
					)}
				</View>

				{/* Time Inputs (only in editing mode) */}
				{isEditingPath && (
					<View style={styles.timeContainer}>
						<View style={styles.timeRow}>
							<Text style={styles.timeLabel}>Start:</Text>
							<TextInput
								style={styles.timeInput}
								value={startTime}
								onChangeText={setStartTime}
								placeholder="HH:MM"
								placeholderTextColor="#999"
							/>
							<Text style={styles.timeLabel}>End:</Text>
							<TextInput
								style={styles.timeInput}
								value={endTime}
								onChangeText={setEndTime}
								placeholder="HH:MM"
								placeholderTextColor="#999"
							/>
						</View>
					</View>
				)}

				{/* Tracking Info (only when tracking) */}
				{trackingStatus === "tracking" && (
					<View style={styles.infoRow}>
						<View style={styles.infoItem}>
							<Text style={styles.infoLabel}>Speed</Text>
							<Text style={styles.infoValue}>{speed} km/h</Text>
						</View>
						<View style={styles.infoItem}>
							<Text style={styles.infoLabel}>Distance</Text>
							<Text style={styles.infoValue}>
								{distanceRemaining} km
							</Text>
						</View>
						<View style={styles.infoItem}>
							<Text style={styles.infoLabel}>ETA</Text>
							<Text style={styles.infoValue}>{eta}</Text>
						</View>
						<View style={styles.infoItem}>
							<Text style={styles.infoLabel}>Progress</Text>
							<Text style={styles.infoValue}>
								{Math.round(progress * 100)}%
							</Text>
						</View>
					</View>
				)}

				{/* Action Buttons */}
				<View style={styles.buttonContainer}>
					{isEditingPath ? (
						<TouchableOpacity
							style={[
								styles.actionButton,
								(!startPos || !endPos) && styles.actionButtonDisabled,
							]}
							onPress={startTracking}
							disabled={!startPos || !endPos}
						>
							<Text style={styles.actionButtonText}>Start Tracking</Text>
						</TouchableOpacity>
					) : trackingStatus === "tracking" ? (
						<TouchableOpacity
							style={[styles.actionButton, styles.stopButton]}
							onPress={() => stopTracking("Tracking paused")}
						>
							<Text style={styles.actionButtonText}>Stop</Text>
						</TouchableOpacity>
					) : (
						<TouchableOpacity
							style={styles.actionButton}
							onPress={startTracking}
						>
							<Text style={styles.actionButtonText}>
								Resume Tracking
							</Text>
						</TouchableOpacity>
					)}
				</View>

				{/* Instructions */}
				{isEditingPath && !startPos && (
					<Text style={styles.instructions}>
						Tap on the map to set the starting position
					</Text>
				)}
				{isEditingPath && startPos && !endPos && (
					<Text style={styles.instructions}>
						Tap on the map to set the destination
					</Text>
				)}
			</View>
		</View>
	);
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
		backgroundColor: "#fff",
	},
	header: {
		flexDirection: "row",
		justifyContent: "space-between",
		alignItems: "center",
		padding: 16,
		paddingTop: 50,
		backgroundColor: "#fff",
		borderBottomWidth: 1,
		borderBottomColor: "#e0e0e0",
	},
	headerTitle: {
		fontSize: 20,
		fontWeight: "bold",
		color: "#007AFF",
	},
	editButton: {
		paddingHorizontal: 16,
		paddingVertical: 8,
		backgroundColor: "#007AFF",
		borderRadius: 8,
	},
	editButtonText: {
		color: "#fff",
		fontWeight: "600",
		fontSize: 14,
	},
	mapContainer: {
		flex: 1,
	},
	map: {
		width: "100%",
		height: "100%",
	},
	bottomPanel: {
		backgroundColor: "#fff",
		padding: 16,
		paddingBottom: 30,
		borderTopWidth: 1,
		borderTopColor: "#e0e0e0",
	},
	statusContainer: {
		marginBottom: 12,
	},
	statusMessage: {
		fontSize: 16,
		fontWeight: "600",
		color: "#333",
		textAlign: "center",
	},
	stopTimer: {
		fontSize: 14,
		color: "#FF6B35",
		textAlign: "center",
		marginTop: 4,
	},
	timeContainer: {
		marginBottom: 12,
	},
	timeRow: {
		flexDirection: "row",
		justifyContent: "center",
		alignItems: "center",
		gap: 8,
		marginBottom: 8,
	},
	timeLabel: {
		fontSize: 14,
		color: "#666",
		fontWeight: "500",
	},
	timeInput: {
		width: 70,
		paddingHorizontal: 12,
		paddingVertical: 8,
		backgroundColor: "#f0f0f0",
		borderRadius: 8,
		fontSize: 14,
		color: "#333",
		textAlign: "center",
	},
	infoRow: {
		flexDirection: "row",
		justifyContent: "space-around",
		marginBottom: 12,
		paddingVertical: 12,
		backgroundColor: "#f8f9fa",
		borderRadius: 8,
	},
	infoItem: {
		alignItems: "center",
	},
	infoLabel: {
		fontSize: 12,
		color: "#666",
		marginBottom: 4,
	},
	infoValue: {
		fontSize: 16,
		fontWeight: "bold",
		color: "#007AFF",
	},
	buttonContainer: {
		marginBottom: 12,
	},
	actionButton: {
		padding: 16,
		backgroundColor: "#007AFF",
		borderRadius: 12,
		alignItems: "center",
	},
	actionButtonDisabled: {
		backgroundColor: "#ccc",
	},
	actionButtonText: {
		color: "#fff",
		fontSize: 16,
		fontWeight: "600",
	},
	stopButton: {
		backgroundColor: "#FF3B30",
	},
	instructions: {
		fontSize: 13,
		color: "#999",
		textAlign: "center",
		fontStyle: "italic",
	},
});
