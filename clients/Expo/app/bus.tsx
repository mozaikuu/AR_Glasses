import React, { useState, useEffect, useRef, useCallback } from "react";
import {
	View,
	Text,
	TouchableOpacity,
	StyleSheet,
	Dimensions,
	Alert,
	TextInput,
	ScrollView,
	Modal,
} from "react-native";
import { WebView } from "react-native-webview";

const { width, height } = Dimensions.get("window");

// Default region (Cairo, Egypt)
const INITIAL_CENTER = {
	latitude: 31.04,
	longitude: 31.38,
	zoom: 13,
};

type Position = {
	latitude: number;
	longitude: number;
};

type TrackingStatus = "idle" | "tracking" | "stopped";

type SavedTrack = {
	id: string;
	name: string;
	waypoints: Position[];
	startTime: string;
	endTime: string;
	createdAt: string;
};

export default function Bus() {
	// Path setup state - multiple waypoints
	const [waypoints, setWaypoints] = useState<Position[]>([]);
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

	// Saved tracks state
	const [savedTracks, setSavedTracks] = useState<SavedTrack[]>([]);
	const [showSaveModal, setShowSaveModal] = useState(false);
	const [trackName, setTrackName] = useState("");
	const [showSavedTracks, setShowSavedTracks] = useState(false);

	// Refs
	const webViewRef = useRef<WebView>(null);
	const trackingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(
		null,
	);

	// Load saved tracks on mount
	useEffect(() => {
		// Load from AsyncStorage or use defaults
		const defaultTracks: SavedTrack[] = [];
		setSavedTracks(defaultTracks);
	}, []);

	// Generate a straight route between two points (no curve)
	const generateRoute = (start: Position, end: Position): Position[] => {
		const points: Position[] = [];
		const steps = 50; // Number of points in the route

		for (let i = 0; i <= steps; i++) {
			const t = i / steps;
			// Simple linear interpolation (straight line)
			const lat = start.latitude + (end.latitude - start.latitude) * t;
			const lng = start.longitude + (end.longitude - start.longitude) * t;

			points.push({
				latitude: lat,
				longitude: lng,
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

	// Process map click to add waypoints
	useEffect(() => {
		if (mapClickPos && isEditingPath && trackingStatus !== "tracking") {
			setWaypoints((prev) => {
				const newWaypoints = [...prev, mapClickPos];
				const count = newWaypoints.length;

				if (count === 1) {
					setStatusMessage(
						"1 point set. Tap to add more or start tracking",
					);
				} else if (count === 2) {
					setStatusMessage("2 points set. Add more or start tracking");
				} else {
					setStatusMessage(
						`${count} points set. Add more or start tracking`,
					);
				}

				return newWaypoints;
			});
			setMapClickPos(null);
		}
	}, [mapClickPos, isEditingPath, trackingStatus]);

	// Send commands to WebView
	const sendToWebView = useCallback((data: any) => {
		if (webViewRef.current) {
			webViewRef.current.postMessage(JSON.stringify(data));
		}
	}, []);

	// Update map markers and route
	useEffect(() => {
		sendToWebView({
			type: "updateMap",
			waypoints: waypoints,
			startPos: waypoints.length > 0 ? waypoints[0] : null,
			endPos: waypoints.length > 0 ? waypoints[waypoints.length - 1] : null,
			currentPos,
			route: generatedRoute,
			center: waypoints.length > 0 ? waypoints[0] : INITIAL_CENTER,
		});
	}, [waypoints, currentPos, generatedRoute, sendToWebView]);

	// Save current track
	const saveTrack = () => {
		if (waypoints.length < 2) {
			Alert.alert("Error", "Please set at least 2 points first");
			return;
		}
		if (!trackName.trim()) {
			Alert.alert("Error", "Please enter a track name");
			return;
		}

		const newTrack: SavedTrack = {
			id: Date.now().toString(),
			name: trackName.trim(),
			waypoints: [...waypoints],
			startTime,
			endTime,
			createdAt: new Date().toISOString(),
		};

		setSavedTracks((prev) => [...prev, newTrack]);
		setTrackName("");
		setShowSaveModal(false);
		Alert.alert("Success", `Track "${newTrack.name}" saved!`);
	};

	// Load a saved track
	const loadTrack = (track: SavedTrack) => {
		setWaypoints(track.waypoints);
		setStartTime(track.startTime);
		setEndTime(track.endTime);
		setShowSavedTracks(false);
		setStatusMessage(`Loaded "${track.name}" - press Start Tracking`);
	};

	// Delete a saved track
	const deleteTrack = (trackId: string) => {
		Alert.alert(
			"Delete Track",
			"Are you sure you want to delete this track?",
			[
				{ text: "Cancel", style: "cancel" },
				{
					text: "Delete",
					style: "destructive",
					onPress: () => {
						setSavedTracks((prev) =>
							prev.filter((t) => t.id !== trackId),
						);
					},
				},
			],
		);
	};

	// Start tracking
	const startTracking = () => {
		if (waypoints.length < 2) {
			Alert.alert("Error", "Please set at least 2 points on the map");
			return;
		}

		// Generate route from waypoints
		let fullRoute: Position[] = [];
		for (let i = 0; i < waypoints.length - 1; i++) {
			const segment = generateRoute(waypoints[i], waypoints[i + 1]);
			fullRoute = fullRoute.concat(segment);
		}
		setGeneratedRoute(fullRoute);

		setIsEditingPath(false);
		setTrackingStatus("tracking");
		setProgress(0);
		setCurrentPos(waypoints[0]);
		setIsStopped(false);
		setStopReason("");

		// Calculate total distance
		let totalDistance = 0;
		for (let i = 1; i < fullRoute.length; i++) {
			totalDistance += calculateDistance(fullRoute[i - 1], fullRoute[i]);
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
				const routeIndex = Math.floor(newProgress * (fullRoute.length - 1));
				const currentRoutePos = fullRoute[routeIndex];
				setCurrentPos(currentRoutePos);

				// Update speed with some variation
				const newSpeed = 20 + Math.random() * 30; // 20-50 km/h
				setSpeed(Math.round(newSpeed));

				// Update distance remaining
				let remaining = 0;
				for (let i = routeIndex; i < fullRoute.length - 1; i++) {
					remaining += calculateDistance(fullRoute[i], fullRoute[i + 1]);
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
		setWaypoints([]);
		setGeneratedRoute([]);
		setProgress(0);
		setCurrentPos(null);
		setStatusMessage("Tap map to add waypoints");
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

	// Alternative HTML using OpenStreetMap with Leaflet (fallback)
	const osmMapHtml = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { overflow: hidden; }
        #map { width: 100%; height: 100vh; position: absolute; top: 0; left: 0; right: 0; bottom: 0; }
        .waypoint-marker { font-weight: bold; font-size: 12px; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map', {
            zoomControl: true,
            attributionControl: false
        }).setView([30.0444, 31.2357], 13);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            crossOrigin: true
        }).addTo(map);

        var markers = {};
        var polyline = null;
        var waypointMarkers = [];

        // Create custom marker icon
        function createMarkerIcon(color, label) {
            return L.divIcon({
                html: '<div style="background:' + color + ';width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;font-size:13px;border:2px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3);">' + label + '</div>',
                className: 'custom-marker',
                iconSize: [28, 28],
                iconAnchor: [14, 14]
            });
        }

        // Create numbered waypoint marker
        function createWaypointMarker(index) {
            return L.divIcon({
                html: '<div style="background:#FF6B35;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;font-size:11px;border:2px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3);">' + (index + 1) + '</div>',
                className: 'waypoint-marker',
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            });
        }

        // Handle map clicks
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

        // Handle messages from React Native
        document.addEventListener('message', function(e) {
            try {
                var data = JSON.parse(e.data);
                if (data.type === 'updateMap') {
                    // Clear existing markers
                    Object.keys(markers).forEach(function(key) {
                        if (markers[key]) {
                            map.removeLayer(markers[key]);
                        }
                    });
                    markers = {};

                    // Clear waypoint markers
                    waypointMarkers.forEach(function(m) {
                        map.removeLayer(m);
                    });
                    waypointMarkers = [];

                    // Clear existing polyline
                    if (polyline) {
                        map.removeLayer(polyline);
                        polyline = null;
                    }

                    // Add waypoints (numbered markers)
                    if (data.waypoints && data.waypoints.length > 0) {
                        data.waypoints.forEach(function(wp, index) {
                            var label = index === 0 ? 'S' : (index === data.waypoints.length - 1 ? 'E' : '');
                            var marker;
                            if (label) {
                                marker = L.marker([wp.latitude, wp.longitude], {
                                    icon: createMarkerIcon(index === 0 ? '#34C759' : '#FF3B30', label)
                                }).addTo(map);
                            } else {
                                marker = L.marker([wp.latitude, wp.longitude], {
                                    icon: createWaypointMarker(index)
                                }).addTo(map);
                            }
                            waypointMarkers.push(marker);
                        });

                        // Draw polyline connecting waypoints
                        if (data.waypoints.length > 1) {
                            var wpLinePoints = data.waypoints.map(function(p) { return [p.latitude, p.longitude]; });
                            L.polyline(wpLinePoints, {
                                color: '#FF6B35',
                                weight: 3,
                                opacity: 0.6,
                                dashArray: '5, 10'
                            }).addTo(map);
                        }
                    }

                    // Add current position marker (bus)
                    if (data.currentPos) {
                        markers.current = L.marker([data.currentPos.latitude, data.currentPos.longitude], {
                            icon: createMarkerIcon('#007AFF', '🚌')
                        }).addTo(map);
                    }

                    // Add route polyline (generated route)
                    if (data.route && data.route.length > 0) {
                        var routePoints = data.route.map(function(p) { return [p.latitude, p.longitude]; });
                        polyline = L.polyline(routePoints, { 
                            color: '#007AFF', 
                            weight: 4,
                            opacity: 0.8
                        }).addTo(map);
                    }

                    // Only pan/zoom on initial load or when waypoints change significantly
                    if (data.waypoints && data.waypoints.length > 0) {
                        // Only fit bounds if this is the first time showing waypoints or if route changed
                        if (!window.mapBoundsSet || data.forceFit) {
                            var first = data.waypoints[0];
                            var last = data.waypoints[data.waypoints.length - 1];
                            var bounds = L.latLngBounds([
                                [first.latitude, first.longitude],
                                [last.latitude, last.longitude]
                            ]);
                            map.fitBounds(bounds, { padding: [50, 50] });
                            window.mapBoundsSet = true;
                        }
                        
                        // Update center for bus tracking without zooming
                        if (data.currentPos && window.mapBoundsSet) {
                            map.panTo([data.currentPos.latitude, data.currentPos.longitude], { animate: true });
                        }
                    } else if (data.center) {
                        map.setView([data.center.latitude, data.center.longitude], data.center.zoom || 13);
                    }
                }
            } catch (err) {
                console.error('Error parsing message:', err);
            }
        });

        // Notify that map is ready
        if (window.ReactNativeWebView) {
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'mapReady' }));
        }
    </script>
</body>
</html>
	`;

	return (
		<View style={styles.container}>
			{/* Header */}
			<View style={styles.header}>
				<Text style={styles.headerTitle}>Bus Tracking</Text>
				<View style={styles.headerButtons}>
					{!isEditingPath && (
						<TouchableOpacity
							style={styles.editButton}
							onPress={editPath}
						>
							<Text style={styles.editButtonText}>Edit Path</Text>
						</TouchableOpacity>
					)}
					<TouchableOpacity
						style={styles.savedButton}
						onPress={() => setShowSavedTracks(!showSavedTracks)}
					>
						<Text style={styles.savedButtonText}>
							{showSavedTracks ? "Hide" : "Saved"}
						</Text>
					</TouchableOpacity>
				</View>
			</View>

			{/* Saved Tracks Panel */}
			{showSavedTracks && (
				<View style={styles.savedTracksPanel}>
					<Text style={styles.savedTracksTitle}>Saved Tracks</Text>
					{savedTracks.length === 0 ? (
						<Text style={styles.noTracksText}>No saved tracks yet</Text>
					) : (
						<ScrollView style={styles.savedTracksList}>
							{savedTracks.map((track) => (
								<View key={track.id} style={styles.trackItem}>
									<View style={styles.trackInfo}>
										<Text style={styles.trackName}>{track.name}</Text>
										<Text style={styles.trackDetails}>
											{track.waypoints.length} points |{" "}
											{track.startTime} - {track.endTime}
										</Text>
									</View>
									<View style={styles.trackButtons}>
										<TouchableOpacity
											style={styles.loadButton}
											onPress={() => loadTrack(track)}
										>
											<Text style={styles.loadButtonText}>Load</Text>
										</TouchableOpacity>
										<TouchableOpacity
											style={styles.deleteButton}
											onPress={() => deleteTrack(track.id)}
										>
											<Text style={styles.deleteButtonText}>
												Delete
											</Text>
										</TouchableOpacity>
									</View>
								</View>
							))}
						</ScrollView>
					)}
				</View>
			)}

			{/* Map (WebView with OpenStreetMap/Leaflet) */}
			<View style={styles.mapContainer}>
				<WebView
					ref={webViewRef}
					originWhitelist={["*"]}
					source={{ html: osmMapHtml }}
					style={styles.map}
					onMessage={handleWebViewMessage}
					javaScriptEnabled={true}
					domStorageEnabled={true}
					startInLoadingState={true}
					renderLoading={() => (
						<View style={styles.mapLoading}>
							<Text>Loading map...</Text>
						</View>
					)}
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
								keyboardType="numeric"
							/>
							<Text style={styles.timeLabel}>End:</Text>
							<TextInput
								style={styles.timeInput}
								value={endTime}
								onChangeText={setEndTime}
								placeholder="HH:MM"
								placeholderTextColor="#999"
								keyboardType="numeric"
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
						<>
							<TouchableOpacity
								style={[
									styles.actionButton,
									waypoints.length < 2 && styles.actionButtonDisabled,
								]}
								onPress={startTracking}
								disabled={waypoints.length < 2}
							>
								<Text style={styles.actionButtonText}>
									Start Tracking
								</Text>
							</TouchableOpacity>
							{waypoints.length >= 2 && (
								<TouchableOpacity
									style={[styles.actionButton, styles.saveButton]}
									onPress={() => setShowSaveModal(true)}
								>
									<Text style={styles.actionButtonText}>
										Save Track
									</Text>
								</TouchableOpacity>
							)}
						</>
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
				{isEditingPath && waypoints.length === 0 && (
					<Text style={styles.instructions}>
						Tap on the map to add waypoints along the road
					</Text>
				)}
				{isEditingPath && waypoints.length > 0 && (
					<Text style={styles.instructions}>
						{waypoints.length} point(s) set. Tap to add more or press
						"Start Tracking"
					</Text>
				)}
			</View>

			{/* Save Track Modal */}
			<Modal
				visible={showSaveModal}
				transparent={true}
				animationType="slide"
				onRequestClose={() => setShowSaveModal(false)}
			>
				<View style={styles.modalOverlay}>
					<View style={styles.modalContent}>
						<Text style={styles.modalTitle}>Save Track</Text>
						<TextInput
							style={styles.modalInput}
							placeholder="Track name (e.g., Campus Route)"
							value={trackName}
							onChangeText={setTrackName}
						/>
						<View style={styles.modalButtons}>
							<TouchableOpacity
								style={styles.modalCancelButton}
								onPress={() => setShowSaveModal(false)}
							>
								<Text style={styles.modalButtonText}>Cancel</Text>
							</TouchableOpacity>
							<TouchableOpacity
								style={styles.modalSaveButton}
								onPress={saveTrack}
							>
								<Text style={styles.modalButtonText}>Save</Text>
							</TouchableOpacity>
						</View>
					</View>
				</View>
			</Modal>
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
	headerButtons: {
		flexDirection: "row",
		gap: 8,
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
	savedButton: {
		paddingHorizontal: 16,
		paddingVertical: 8,
		backgroundColor: "#34C759",
		borderRadius: 8,
	},
	savedButtonText: {
		color: "#fff",
		fontWeight: "600",
		fontSize: 14,
	},
	savedTracksPanel: {
		maxHeight: 150,
		backgroundColor: "#f8f9fa",
		padding: 12,
		borderBottomWidth: 1,
		borderBottomColor: "#e0e0e0",
	},
	savedTracksTitle: {
		fontSize: 16,
		fontWeight: "bold",
		color: "#333",
		marginBottom: 8,
	},
	noTracksText: {
		fontSize: 14,
		color: "#999",
		textAlign: "center",
		padding: 8,
	},
	savedTracksList: {
		maxHeight: 100,
	},
	trackItem: {
		flexDirection: "row",
		justifyContent: "space-between",
		alignItems: "center",
		padding: 8,
		backgroundColor: "#fff",
		borderRadius: 8,
		marginBottom: 4,
	},
	trackInfo: {
		flex: 1,
	},
	trackName: {
		fontSize: 14,
		fontWeight: "600",
		color: "#333",
	},
	trackDetails: {
		fontSize: 12,
		color: "#666",
		marginTop: 2,
	},
	trackButtons: {
		flexDirection: "row",
		gap: 8,
	},
	loadButton: {
		paddingHorizontal: 12,
		paddingVertical: 6,
		backgroundColor: "#007AFF",
		borderRadius: 6,
	},
	loadButtonText: {
		color: "#fff",
		fontSize: 12,
		fontWeight: "600",
	},
	deleteButton: {
		paddingHorizontal: 12,
		paddingVertical: 6,
		backgroundColor: "#FF3B30",
		borderRadius: 6,
	},
	deleteButtonText: {
		color: "#fff",
		fontSize: 12,
		fontWeight: "600",
	},
	mapContainer: {
		flex: 1,
	},
	map: {
		width: "100%",
		height: "100%",
	},
	mapLoading: {
		flex: 1,
		justifyContent: "center",
		alignItems: "center",
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
		marginBottom: 8,
	},
	saveButton: {
		backgroundColor: "#34C759",
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
	modalOverlay: {
		flex: 1,
		backgroundColor: "rgba(0,0,0,0.5)",
		justifyContent: "center",
		alignItems: "center",
	},
	modalContent: {
		width: "85%",
		backgroundColor: "#fff",
		borderRadius: 16,
		padding: 24,
	},
	modalTitle: {
		fontSize: 18,
		fontWeight: "bold",
		color: "#333",
		marginBottom: 16,
		textAlign: "center",
	},
	modalInput: {
		width: "100%",
		paddingHorizontal: 16,
		paddingVertical: 12,
		backgroundColor: "#f0f0f0",
		borderRadius: 8,
		fontSize: 16,
		marginBottom: 16,
	},
	modalButtons: {
		flexDirection: "row",
		gap: 12,
	},
	modalCancelButton: {
		flex: 1,
		padding: 14,
		backgroundColor: "#e0e0e0",
		borderRadius: 8,
		alignItems: "center",
	},
	modalSaveButton: {
		flex: 1,
		padding: 14,
		backgroundColor: "#34C759",
		borderRadius: 8,
		alignItems: "center",
	},
	modalButtonText: {
		color: "#fff",
		fontSize: 16,
		fontWeight: "600",
	},
});
