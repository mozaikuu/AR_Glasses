/**
 * Smart Glasses AR Renderer
 *
 * Three.js-based WebGL renderer for AR overlays.
 * Receives camera frames and pose data via WebSocket,
 * renders virtual objects aligned with detected markers.
 */

class ARRenderer {
	constructor() {
		this.scene = null;
		this.camera = null;
		this.renderer = null;
		this.websocket = null;
		this.isConnected = false;

		// Virtual objects
		this.virtualObjects = new Map();
		this.debugObjects = [];

		// Stats
		this.frameCount = 0;
		this.lastFpsUpdate = performance.now();
		this.currentFps = 0;

		// Camera calibration (from phone)
		this.cameraMatrix = null;
		this.distortion = null;

		// Initialize
		this.init();
	}

	init() {
		const canvas = document.getElementById("ar-canvas");
		const video = document.getElementById("camera-feed");

		// Get canvas dimensions
		const width = window.innerWidth;
		const height = window.innerHeight;

		// Setup Three.js
		this.scene = new THREE.Scene();

		// Create camera for rendering
		// Note: This is the virtual camera for rendering
		// The actual camera pose comes from tracking
		this.camera = new THREE.PerspectiveCamera(60, width / height, 0.01, 100);
		this.camera.position.set(0, 0, 0);

		// Setup renderer
		this.renderer = new THREE.WebGLRenderer({
			canvas: canvas,
			alpha: true,
			antialias: true,
		});
		this.renderer.setSize(width, height);
		this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
		this.renderer.setClearColor(0x000000, 0); // Transparent

		// Setup lighting
		const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
		this.scene.add(ambientLight);

		const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
		directionalLight.position.set(1, 1, 1);
		this.scene.add(directionalLight);

		// Create default virtual object (cube at marker)
		this.createDefaultObjects();

		// Setup UI handlers
		this.setupUI();

		// Start render loop
		this.animate();

		// Handle resize
		window.addEventListener("resize", () => this.onResize());
	}

	createDefaultObjects() {
		// Create a simple cube as test object
		const geometry = new THREE.BoxGeometry(0.03, 0.03, 0.03);
		const material = new THREE.MeshPhongMaterial({
			color: 0x00ff88,
			transparent: true,
			opacity: 0.8,
			shininess: 100,
		});

		this.testCube = new THREE.Mesh(geometry, material);
		this.testCube.visible = false;
		this.scene.add(this.testCube);

		// Create coordinate axes
		this.axesHelper = new THREE.AxesHelper(0.05);
		this.axesHelper.visible = false;
		this.scene.add(this.axesHelper);

		// Create a marker outline
		const outlineGeom = new THREE.RingGeometry(0.015, 0.017, 32);
		const outlineMat = new THREE.MeshBasicMaterial({
			color: 0x00d4ff,
			side: THREE.DoubleSide,
			transparent: true,
			opacity: 0.8,
		});
		this.markerOutline = new THREE.Mesh(outlineGeom, outlineMat);
		this.markerOutline.visible = false;
		this.scene.add(this.markerOutline);
	}

	setupUI() {
		const connectBtn = document.getElementById("connect-btn");
		const serverUrl = document.getElementById("server-url");
		const debugOverlay = document.getElementById("debug-overlay");

		connectBtn.addEventListener("click", () => {
			if (this.isConnected) {
				this.disconnect();
			} else {
				this.connect(serverUrl.value);
			}
		});

		debugOverlay.addEventListener("change", (e) => {
			this.setDebugMode(e.target.checked);
		});
	}

	connect(url) {
		console.log("Connecting to:", url);

		this.websocket = new WebSocket(url);

		this.websocket.onopen = () => {
			console.log("Connected");
			this.isConnected = true;
			this.updateConnectionStatus(true);
		};

		this.websocket.onclose = () => {
			console.log("Disconnected");
			this.isConnected = false;
			this.updateConnectionStatus(false);
		};

		this.websocket.onerror = (error) => {
			console.error("WebSocket error:", error);
		};

		this.websocket.onmessage = (event) => {
			this.handleMessage(JSON.parse(event.data));
		};
	}

	disconnect() {
		if (this.websocket) {
			this.websocket.close();
			this.websocket = null;
		}
		this.isConnected = false;
		this.updateConnectionStatus(false);
	}

	updateConnectionStatus(connected) {
		const statusEl = document.getElementById("connection-status");
		const statusText = document.getElementById("status-text");
		const btn = document.getElementById("connect-btn");

		if (connected) {
			statusEl.classList.remove("disconnected");
			statusEl.classList.add("connected");
			statusText.textContent = "Connected";
			btn.textContent = "Disconnect";
		} else {
			statusEl.classList.remove("connected");
			statusEl.classList.add("disconnected");
			statusText.textContent = "Disconnected";
			btn.textContent = "Connect";
		}
	}

	handleMessage(data) {
		const timestamp = performance.now();

		switch (data.type) {
			case "camera_raw":
			case "camera_compressed":
				this.updateCameraFeed(data.data);
				break;

			case "ar_output":
				// Full AR frame (not used when we do overlay)
				break;

			case "pose_data":
				this.updatePose(data);
				break;
		}

		// Update stats
		this.frameCount++;
		const now = performance.now();
		if (now - this.lastFpsUpdate > 1000) {
			this.currentFps = Math.round(
				(this.frameCount * 1000) / (now - this.lastFpsUpdate),
			);
			this.frameCount = 0;
			this.lastFpsUpdate = now;
			document.getElementById("fps").textContent = this.currentFps;
		}

		// Calculate latency
		const latency = data.timestamp ? timestamp - data.timestamp * 1000 : 0;
		document.getElementById("latency").textContent =
			Math.round(latency) + "ms";
	}

	updateCameraFeed(base64Data) {
		const video = document.getElementById("camera-feed");
		video.src = "data:image/jpeg;base64," + base64Data;
	}

	updatePose(poseData) {
		const { rvec, tvec, marker_id } = poseData;

		// Update virtual object position based on pose
		if (this.testCube) {
			// Convert rotation vector to rotation matrix
			const rotationMatrix = this.rodriguesToMatrix(rvec);

			// Create transformation matrix
			const matrix = new THREE.Matrix4();
			matrix.set(
				rotationMatrix[0][0],
				rotationMatrix[0][1],
				rotationMatrix[0][2],
				tvec[0],
				rotationMatrix[1][0],
				rotationMatrix[1][1],
				rotationMatrix[1][2],
				tvec[1],
				rotationMatrix[2][0],
				rotationMatrix[2][1],
				rotationMatrix[2][2],
				tvec[2],
				0,
				0,
				0,
				1,
			);

			// Apply to cube
			this.testCube.position.set(tvec[0], tvec[1], tvec[2]);
			this.testCube.rotation.setFromRotationMatrix(
				new THREE.Matrix4().set(
					rotationMatrix[0][0],
					rotationMatrix[0][1],
					rotationMatrix[0][2],
					0,
					rotationMatrix[1][0],
					rotationMatrix[1][1],
					rotationMatrix[1][2],
					0,
					rotationMatrix[2][0],
					rotationMatrix[2][1],
					rotationMatrix[2][2],
					0,
					0,
					0,
					0,
					1,
				),
			);
			this.testCube.visible = true;

			// Update debug objects
			if (this.axesHelper.visible) {
				this.axesHelper.position.copy(this.testCube.position);
				this.axesHelper.rotation.copy(this.testCube.rotation);
			}

			if (this.markerOutline.visible) {
				this.markerOutline.position.set(tvec[0], tvec[1], tvec[2]);
				this.markerOutline.rotation.setFromRotationMatrix(
					new THREE.Matrix4().set(
						rotationMatrix[0][0],
						rotationMatrix[0][1],
						rotationMatrix[0][2],
						0,
						rotationMatrix[1][0],
						rotationMatrix[1][1],
						rotationMatrix[1][2],
						0,
						rotationMatrix[2][0],
						rotationMatrix[2][1],
						rotationMatrix[2][2],
						0,
						0,
						0,
						0,
						1,
					),
				);
			}
		}

		// Update marker count
		document.getElementById("markers").textContent = "1";
	}

	rodriguesToMatrix(rvec) {
		// Convert Rodrigues rotation vector to 3x3 rotation matrix
		// Simplified - use OpenCV's Rodrigues formula
		const theta = Math.sqrt(
			rvec[0] * rvec[0] + rvec[1] * rvec[1] + rvec[2] * rvec[2],
		);

		if (theta < 0.0001) {
			return [
				[1, 0, 0],
				[0, 1, 0],
				[0, 0, 1],
			];
		}

		const kx = rvec[0] / theta;
		const ky = rvec[1] / theta;
		const kz = rvec[2] / theta;

		const c = Math.cos(theta);
		const s = Math.sin(theta);
		const C = 1 - c;

		// Rotation matrix from Rodrigues formula
		return [
			[kx * kx * C + c, kx * ky * C - kz * s, kx * kz * C + ky * s],
			[ky * kx * C + kz * s, ky * ky * C + c, ky * kz * C - kx * s],
			[kz * kx * C - ky * s, kz * ky * C + kx * s, kz * kz * C + c],
		];
	}

	setCameraCalibration(matrix, distortion) {
		this.cameraMatrix = matrix;
		this.distortion = distortion;

		// Update projection if needed
		if (this.cameraMatrix) {
			// Adjust camera FOV based on intrinsics
			const fx = this.cameraMatrix[0][0];
			const fy = this.cameraMatrix[1][1];
			const width = 640; // Assume 640x480
			const height = 480;

			const fovX = (2 * Math.atan(width / (2 * fx)) * 180) / Math.PI;
			const fovY = (2 * Math.atan(height / (2 * fy)) * 180) / Math.PI;

			this.camera.fov = fovY;
			this.camera.updateProjectionMatrix();
		}
	}

	addVirtualObject(id, mesh) {
		this.virtualObjects.set(id, mesh);
		this.scene.add(mesh);
	}

	removeVirtualObject(id) {
		const mesh = this.virtualObjects.get(id);
		if (mesh) {
			this.scene.remove(mesh);
			this.virtualObjects.delete(id);
		}
	}

	setDebugMode(enabled) {
		this.axesHelper.visible = enabled;
		this.markerOutline.visible = enabled;

		// Make test cube semi-transparent
		if (this.testCube) {
			this.testCube.material.wireframe = enabled;
		}
	}

	onResize() {
		const width = window.innerWidth;
		const height = window.innerHeight;

		this.camera.aspect = width / height;
		this.camera.updateProjectionMatrix();
		this.renderer.setSize(width, height);
	}

	animate() {
		requestAnimationFrame(() => this.animate());

		// Render scene
		this.renderer.render(this.scene, this.camera);
	}
}

// Initialize on load
window.addEventListener("load", () => {
	window.arRenderer = new ARRenderer();
});
