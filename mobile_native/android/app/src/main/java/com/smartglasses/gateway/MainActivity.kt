package com.smartglasses.gateway

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.smartglasses.gateway.service.AudioRecordingService
import com.smartglasses.gateway.service.BleService

/**
 * Main activity for Smart Glasses Gateway app.
 * Handles permission requests and service management.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var statusText: TextView
    private lateinit var startButton: Button
    private lateinit var stopButton: Button

    companion object {
        private const val SERVER_URL = "wss://YOUR_SERVER_IP:8765"
    }

    private val requiredPermissions = mutableListOf<String>().apply {
        add(Manifest.permission.RECORD_AUDIO)
        add(Manifest.permission.INTERNET)
        add(Manifest.permission.ACCESS_NETWORK_STATE)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            add(Manifest.permission.POST_NOTIFICATIONS)
        }
        add(Manifest.permission.BLUETOOTH_CONNECT)
    }

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.entries.all { it.value }
        if (allGranted) {
            updateStatus("Permissions granted. Ready to start.")
            enableButtons(true)
        } else {
            updateStatus("Permissions required. Please grant them in Settings.")
            enableButtons(false)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        statusText = findViewById(R.id.status_text)
        startButton = findViewById(R.id.btn_start)
        stopButton = findViewById(R.id.btn_stop)

        startButton.setOnClickListener {
            if (checkPermissions()) {
                startAudioService()
            } else {
                requestPermissions()
            }
        }

        stopButton.setOnClickListener {
            stopAudioService()
        }

        // Initial state
        updateStatus("Checking permissions...")
        enableButtons(false)
        checkPermissions()
    }

    override fun onResume() {
        super.onResume()
        updateServiceStatus()
    }

    private fun checkPermissions(): Boolean {
        val allGranted = requiredPermissions.all { permission ->
            ContextCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED
        }

        if (!allGranted) {
            updateStatus("Permissions required. Tap 'Start' to request.")
            enableButtons(false)
        } else {
            updateStatus("Permissions granted. Ready to start.")
            enableButtons(true)
        }

        return allGranted
    }

    private fun requestPermissions() {
        permissionLauncher.launch(requiredPermissions.toTypedArray())
    }

    private fun enableButtons(enabled: Boolean) {
        startButton.isEnabled = enabled
        stopButton.isEnabled = enabled
        startButton.alpha = if (enabled) 1.0f else 0.5f
        stopButton.alpha = if (enabled) 1.0f else 0.5f
    }

    private fun updateStatus(message: String) {
        statusText.text = message
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show()
    }

    private fun startAudioService() {
        updateStatus("Starting audio service...")

        val intent = Intent(this, AudioRecordingService::class.java).apply {
            putExtra(AudioRecordingService.EXTRA_SERVER_URL, SERVER_URL)
            putExtra(AudioRecordingService.EXTRA_SAMPLE_RATE, 16000)
            putExtra(AudioRecordingService.EXTRA_BUFFER_SECONDS, 2)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }

        // Also start BLE service
        val bleIntent = Intent(this, BleService::class.java)
        startService(bleIntent)

        updateStatus("Audio service started. Recording in progress.")
    }

    private fun stopAudioService() {
        val intent = Intent(this, AudioRecordingService::class.java)
        stopService(intent)

        updateStatus("Audio service stopped.")
    }

    private fun updateServiceStatus() {
        val isRunning = isServiceRunning(AudioRecordingService::class.java)
        if (isRunning) {
            updateStatus("Audio service is running. Listening...")
            stopButton.isEnabled = true
            stopButton.alpha = 1.0f
        }
    }

    private fun isServiceRunning(serviceClass: Class<*>): Boolean {
        val manager = getSystemService(ACTIVITY_SERVICE) as android.app.ActivityManager
        @Suppress("DEPRECATION")
        for (service in manager.getRunningServices(Int.MAX_VALUE)) {
            if (serviceClass.name == service.service.className) {
                return true
            }
        }
        return false
    }

    override fun onDestroy() {
        super.onDestroy()
        // Service continues running unless user explicitly stops
    }
}
