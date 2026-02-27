package com.smartglasses.gateway.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.AudioTrack
import android.media.MediaRecorder
import android.os.Binder
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import com.smartglasses.gateway.MainActivity
import com.smartglasses.gateway.R
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import okio.ByteString
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Foreground service for continuous audio recording and streaming.
 * Runs as a foreground service with persistent notification.
 *
 * Key features:
 * - Continuous PCM audio capture at 16kHz mono
 * - WebSocket streaming to server
 * - Automatic reconnection on disconnect
 * - Audio playback support for responses
 */
class AudioRecordingService : Service() {

    companion object {
        private const val TAG = "AudioRecordingService"

        const val EXTRA_SERVER_URL = "server_url"
        const val EXTRA_SAMPLE_RATE = "sample_rate"
        const val EXTRA_BUFFER_SECONDS = "buffer_seconds"

        private const val CHANNEL_ID = "audio_recording_channel"
        private const val NOTIFICATION_ID = 1001

        // Audio configuration
        private const val DEFAULT_SAMPLE_RATE = 16000
        private const val DEFAULT_BUFFER_SECONDS = 2
        private const val CHANNEL_CONFIG = AudioFormat.CHANNEL_IN_MONO
        private const val AUDIO_FORMAT = AudioFormat.ENCODING_PCM_16BIT

        // WebSocket reconnection
        private const val RECONNECT_DELAY_MS = 1000L
        private const val MAX_RECONNECT_ATTEMPTS = 10
        private const val MAX_BLE_TEXT_LEN = 180
    }

    // Audio recording
    private var audioRecord: AudioRecord? = null
    private var recordingThread: Thread? = null
    private val isRecording = AtomicBoolean(false)

    // Audio playback
    private var audioTrack: AudioTrack? = null
    private var playbackThread: Thread? = null
    private val isPlaying = AtomicBoolean(false)

    // WebSocket connection
    private var serverUrl: String = ""
    private var webSocket: WebSocket? = null
    private var okHttpClient: OkHttpClient? = null
    private var reconnectAttempts = 0

    // Binder for activity binding
    private val binder = LocalBinder()

    // Coroutines
    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    // Audio buffer
    private val audioBuffer = ByteArrayOutputStream()
    private var sampleRate = DEFAULT_SAMPLE_RATE
    private var bufferSizeInBytes: Int = 0
    private var receiverRegistered = false

    private val bleMessageReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action != BleService.ACTION_BLE_RX_TEXT) return
            val message = intent.getStringExtra(BleService.EXTRA_TEXT)?.trim().orEmpty()
            if (message.isEmpty()) return
            handleBleTextMessage(message)
        }
    }

    inner class LocalBinder : Binder() {
        fun getService(): AudioRecordingService = this@AudioRecordingService
    }

    override fun onBind(intent: Intent?): IBinder = binder

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        initializeAudio()
        initializeHttpClient()
        registerBleReceiver()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // Start as foreground service
        startForeground(NOTIFICATION_ID, createNotification("Recording audio..."))

        // Get configuration from intent
        serverUrl = intent?.getStringExtra(EXTRA_SERVER_URL)
            ?: "wss://${getServerIpFromConfig()}:8765"
        sampleRate = intent?.getIntExtra(EXTRA_SAMPLE_RATE, DEFAULT_SAMPLE_RATE)
            ?: DEFAULT_SAMPLE_RATE
        val bufferSeconds = intent?.getIntExtra(EXTRA_BUFFER_SECONDS, DEFAULT_BUFFER_SECONDS)
            ?: DEFAULT_BUFFER_SECONDS

        bufferSizeInBytes = sampleRate * bufferSeconds * 2 // 16-bit = 2 bytes

        // Start recording
        startRecording()

        // Connect WebSocket
        connectWebSocket()

        return START_STICKY // Restart if killed by system
    }

    override fun onDestroy() {
        unregisterBleReceiver()
        stopRecording()
        stopPlayback()
        disconnectWebSocket()
        serviceScope.cancel()
        super.onDestroy()
    }

    override fun onTaskRemoved(rootIntent: Intent?) {
        super.onTaskRemoved(rootIntent)
        // Restart service when task is removed
        val restartIntent = Intent(applicationContext, AudioRecordingService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(restartIntent)
        } else {
            startService(restartIntent)
        }
    }

    // ==================== Audio Recording ====================

    private fun initializeAudio() {
        // Calculate minimum buffer size
        bufferSizeInBytes = AudioRecord.getMinBufferSize(
            sampleRate,
            CHANNEL_CONFIG,
            AUDIO_FORMAT
        )

        if (bufferSizeInBytes == AudioRecord.ERROR_BAD_VALUE ||
            bufferSizeInBytes == AudioRecord.ERROR
        ) {
            Log.e(TAG, "Invalid buffer size: $bufferSizeInBytes")
            bufferSizeInBytes = sampleRate * 2 * 2 // Default to 2 seconds
        }

        Log.d(TAG, "Audio initialized with sample rate: $sampleRate, buffer: $bufferSizeInBytes")
    }

    private fun startRecording() {
        if (isRecording.get()) {
            Log.w(TAG, "Already recording")
            return
        }

        try {
            audioRecord = AudioRecord(
                MediaRecorder.AudioSource.MIC,
                sampleRate,
                CHANNEL_CONFIG,
                AUDIO_FORMAT,
                bufferSizeInBytes
            )

            if (audioRecord?.state != AudioRecord.STATE_INITIALIZED) {
                Log.e(TAG, "AudioRecord failed to initialize")
                return
            }

            audioRecord?.startRecording()
            isRecording.set(true)

            // Start recording thread
            recordingThread = Thread {
                recordAudio()
            }.apply { start() }

            Log.i(TAG, "Audio recording started")
            updateNotification("Recording audio...")

        } catch (e: SecurityException) {
            Log.e(TAG, "Microphone permission not granted", e)
            stopSelf()
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start audio recording", e)
        }
    }

    private fun stopRecording() {
        if (!isRecording.get()) return

        isRecording.set(false)

        try {
            audioRecord?.stop()
            audioRecord?.release()
            audioRecord = null
        } catch (e: Exception) {
            Log.e(TAG, "Error stopping AudioRecord", e)
        }

        recordingThread?.interrupt()
        recordingThread = null

        Log.i(TAG, "Audio recording stopped")
    }

    private fun recordAudio() {
        val buffer = ShortArray(bufferSizeInBytes / 2)

        while (isRecording.get() && audioRecord != null) {
            try {
                val readCount = audioRecord?.read(buffer, 0, buffer.size) ?: -1

                if (readCount > 0) {
                    // Convert to byte array
                    val byteBuffer = ByteArray(readCount * 2)
                    buffer.forEachIndexed { index, value ->
                        byteBuffer[index * 2] = (value.toInt() and 0xFF).toByte()
                        byteBuffer[index * 2 + 1] = (value.toInt() shr 8).toByte()
                    }

                    // Send to WebSocket
                    sendAudioToServer(byteBuffer)

                    // Accumulate for local processing (optional)
                    synchronized(audioBuffer) {
                        audioBuffer.write(byteBuffer)
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error reading audio", e)
                if (!isRecording.get()) break
            }
        }
    }

    // ==================== Audio Playback ====================

    private fun initializePlayback() {
        val bufferSize = AudioTrack.getMinBufferSize(
            sampleRate,
            AudioFormat.CHANNEL_OUT_MONO,
            AUDIO_FORMAT
        )

        audioTrack = AudioTrack.Builder()
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_VOICE_COMMUNICATION)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                    .build()
            )
            .setAudioFormat(
                AudioFormat.Builder()
                    .setEncoding(AUDIO_FORMAT)
                    .setSampleRate(sampleRate)
                    .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                    .build()
            )
            .setBufferSizeInBytes(bufferSize)
            .setTransferMode(AudioTrack.MODE_STREAM)
            .build()
    }

    private fun playAudio(audioData: ByteArray) {
        if (isPlaying.get()) return

        if (audioTrack == null) {
            initializePlayback()
        }

        isPlaying.set(true)

        playbackThread = Thread {
            try {
                audioTrack?.write(audioData, 0, audioData.size)
            } catch (e: Exception) {
                Log.e(TAG, "Error playing audio", e)
            } finally {
                isPlaying.set(false)
            }
        }.apply { start() }
    }

    private fun stopPlayback() {
        if (!isPlaying.get()) return

        isPlaying.set(false)

        try {
            audioTrack?.stop()
            audioTrack?.release()
            audioTrack = null
        } catch (e: Exception) {
            Log.e(TAG, "Error stopping AudioTrack", e)
        }

        playbackThread?.interrupt()
        playbackThread = null
    }

    // ==================== WebSocket ====================

    private fun initializeHttpClient() {
        okHttpClient = OkHttpClient.Builder()
            .pingInterval(30, TimeUnit.SECONDS)
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }

    private fun connectWebSocket() {
        if (serverUrl.isEmpty()) {
            Log.e(TAG, "Server URL not configured")
            return
        }

        val request = Request.Builder()
            .url(serverUrl)
            .addHeader("X-Device-Type", "android")
            .addHeader("X-App-Version", "1.0.0")
            .build()

        webSocket = okHttpClient?.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: okhttp3.Response) {
                Log.i(TAG, "WebSocket connected")
                reconnectAttempts = 0
                updateNotification("Connected to server")
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                // Handle text message (commands, responses)
                handleServerMessage(text)
            }

            override fun onMessage(webSocket: WebSocket, bytes: ByteString) {
                // Handle binary message (audio response)
                playAudio(bytes.toByteArray())
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                Log.i(TAG, "WebSocket closing: $reason")
                webSocket.close(1000, null)
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                Log.i(TAG, "WebSocket closed: $reason")
                scheduleReconnect()
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: okhttp3.Response?) {
                Log.e(TAG, "WebSocket failure", t)
                scheduleReconnect()
            }
        })
    }

    private fun sendAudioToServer(audioData: ByteArray) {
        webSocket?.send(ByteString.of(*audioData))
    }

    private fun disconnectWebSocket() {
        webSocket?.close(1000, "Service stopped")
        webSocket = null
    }

    private fun scheduleReconnect() {
        if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
            Log.e(TAG, "Max reconnect attempts reached")
            updateNotification("Connection failed. Tap to retry.")
            return
        }

        reconnectAttempts++
        val delay = RECONNECT_DELAY_MS * reconnectAttempts

        Log.i(TAG, "Scheduling reconnect attempt $reconnectAttempts in ${delay}ms")

        serviceScope.launch {
            kotlinx.coroutines.delay(delay)
            connectWebSocket()
        }
    }

    private fun handleServerMessage(message: String) {
        try {
            val json = JSONObject(message)
            val type = json.optString("type", "")
            when (type) {
                "response", "text", "command" -> {
                    val text = json.optString("text", "").trim()
                    if (text.isNotEmpty()) {
                        forwardTextToBle("TTS:${limitForBle(text)}")
                        Log.d(TAG, "Forwarded server text to BLE: $text")
                    }
                }
                "status" -> {
                    Log.d(TAG, "Server status: $message")
                }
                else -> {
                    Log.d(TAG, "Server message: $message")
                }
            }
        } catch (_: Exception) {
            Log.d(TAG, "Non-JSON server message: $message")
        }
    }

    private fun handleBleTextMessage(message: String) {
        Log.d(TAG, "BLE message received: $message")
        if (message.startsWith("CMD:")) {
            val commandText = message.removePrefix("CMD:").trim()
            if (commandText.isNotEmpty()) {
                sendTextCommandToServer(commandText)
            }
            return
        }

        if (message == "PING") {
            forwardTextToBle("PONG")
        }
    }

    private fun sendTextCommandToServer(commandText: String) {
        if (webSocket == null) {
            Log.w(TAG, "WebSocket not connected, text command dropped: $commandText")
            return
        }

        val payload = JSONObject()
            .put("type", "text_command")
            .put("text", commandText)
            .put("source", "ble_esp32")
            .toString()

        webSocket?.send(payload)
        Log.i(TAG, "Sent text command to server: $commandText")
    }

    private fun forwardTextToBle(text: String) {
        val intent = Intent(BleService.ACTION_BLE_TX_TEXT).apply {
            putExtra(BleService.EXTRA_TEXT, text)
            `package` = packageName
        }
        sendBroadcast(intent)
    }

    private fun limitForBle(text: String): String {
        return if (text.length <= MAX_BLE_TEXT_LEN) text else text.take(MAX_BLE_TEXT_LEN)
    }

    // ==================== Configuration ====================

    private fun getServerIpFromConfig(): String {
        // Read from shared preferences or assets
        // For prototype, use localhost or configurable value
        return "localhost"
    }

    // ==================== Notifications ====================

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Audio Recording",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Shows when Smart Glasses Gateway is recording audio"
                setShowBadge(false)
            }

            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
    }

    private fun createNotification(status: String): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Smart Glasses Gateway")
            .setContentText(status)
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setOngoing(true)
            .setContentIntent(pendingIntent)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .build()
    }

    private fun updateNotification(status: String) {
        val notification = createNotification(status)
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE)
            as NotificationManager
        notificationManager.notify(NOTIFICATION_ID, notification)
    }

    // ==================== Public API ====================

    fun isRecording(): Boolean = isRecording.get()

    fun getAudioBuffer(): ByteArray {
        synchronized(audioBuffer) {
            val data = audioBuffer.toByteArray()
            audioBuffer.reset()
            return data
        }
    }

    fun setServerUrl(url: String) {
        if (isRecording.get()) {
            disconnectWebSocket()
            serverUrl = url
            connectWebSocket()
        } else {
            serverUrl = url
        }
    }

    private fun registerBleReceiver() {
        if (receiverRegistered) return
        val filter = IntentFilter(BleService.ACTION_BLE_RX_TEXT)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(bleMessageReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            @Suppress("DEPRECATION")
            registerReceiver(bleMessageReceiver, filter)
        }
        receiverRegistered = true
    }

    private fun unregisterBleReceiver() {
        if (!receiverRegistered) return
        unregisterReceiver(bleMessageReceiver)
        receiverRegistered = false
    }
}
