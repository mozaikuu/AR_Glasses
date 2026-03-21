# ngrok HTTPS Microphone Issue - Solutions

## Problem

When using ngrok for HTTPS tunneling to access the Smart Glasses server from mobile devices, the microphone doesn't work due to browser security restrictions.

## Root Cause

1. **Browser Security**: Modern browsers require HTTPS with a valid, trusted certificate for microphone access
2. **ngrok Certificate**: ngrok provides HTTPS but the certificate is self-signed and not trusted by mobile OS
3. **Secure Context**: Microphone access requires a "secure context" (HTTPS with trusted cert)

## Solutions

### Solution 1: Use Local IP (Recommended for Development)

Instead of ngrok, use the local network IP from your PC:

1. Get your PC's local IP:

   ```bash
   # Windows
   ipconfig

   # Linux/Mac
   ifconfig
   ```

2. Configure the mobile app to use your PC's IP:

   -  Update `mobile/lib/config.dart`:

   ```dart
   static const String serverUrl = 'http://YOUR_PC_IP:8001';
   ```

3. Ensure both devices are on the same WiFi network

### Solution 2: Use ngrok with Custom Domain + Trusted Certificate

For production, use a custom domain with a trusted certificate:

1. Purchase a domain or use a free one (e.g., from freenom)
2. Configure ngrok with custom domain:
   ```bash
   ngrok http 8000 --domain=your-domain.ngrok.io
   ```
3. Get an SSL certificate from Let's Encrypt
4. Configure ngrok to use your certificate

### Solution 3: Use Cloudflare Tunnel (Free + Trusted Certs)

Cloudflare provides free tunnels with trusted certificates:

1. Install cloudflared
2. Create a free Cloudflare account
3. Set up a tunnel:
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```
4. Use the provided HTTPS URL - certificates are trusted

### Solution 4: Use serveo.net (SSH-based, Free)

Simple SSH-based tunneling without certificate issues:

```bash
ssh -R 80:localhost:8000 serveo.net
```

### Solution 5: Use localtunnel (Node.js based)

```bash
npx localtunnel --port 8000
```

## Mobile App Microphone Permission Checklist

### Android

1. Go to Settings → Apps → Your App → Permissions
2. Enable Microphone permission
3. For Chrome: Settings → Site Settings → Microphone → Allow

### iOS

1. Go to Settings → Privacy → Microphone
2. Enable for your app and Safari
3. For Safari: Settings → Safari → Microphone → Allow

## Testing Microphone Access

Create a simple test HTML file:

```html
<!DOCTYPE html>
<html>
	<head>
		<title>Mic Test</title>
	</head>
	<body>
		<button id="startBtn">Start Recording</button>
		<button id="stopBtn" disabled>Stop Recording</button>
		<p id="status"></p>
		<script>
			let mediaRecorder;
			let audioChunks = [];

			startBtn.onclick = async () => {
				try {
					const stream = await navigator.mediaDevices.getUserMedia({
						audio: true,
					});
					status.textContent = "Microphone access granted!";
					// Continue with recording logic...
				} catch (err) {
					status.textContent = "Error: " + err.message;
				}
			};
		</script>
	</body>
</html>
```

## Quick Fix for Current Setup

For immediate testing without ngrok:

1. Run server locally: `python start_server.py`
2. Find your local IP from the console output
3. On mobile: Use Chrome and navigate to `http://YOUR_PC_IP:8000`
4. Accept any security warnings (HTTP is allowed on local networks)

## Browser Console Debugging

Check browser console (DevTools) for error messages:

-  `NotAllowedError`: Permission denied
-  `NotReadableError`: Device in use
-  `OverconstrainedError`: Audio config issue

## Server-Side Audio Endpoints

Ensure your server supports these endpoints:

-  `POST /v2/voice/transcribe` - Transcribe audio
-  `POST /v2/voice/process` - Process voice commands
-  `GET /health` - Health check

## Docker Solution (Production)

For production with trusted certificates:

```bash
# Use nginx with let's encrypt
docker run -p 80:80 -p 443:443 -v /data/letsencrypt:/etc/letsencrypt nginx:alpine
```
