package com.smartglasses.gateway.service

import android.annotation.SuppressLint
import android.app.Service
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattDescriptor
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.bluetooth.BluetoothSocket
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import androidx.core.app.ServiceCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import java.io.IOException
import java.io.InputStream
import java.io.OutputStream
import java.util.UUID
import java.util.concurrent.ConcurrentLinkedQueue

/**
 * BLE service for communication with Smart Glasses.
 * Handles device discovery, connection, and data transmission.
 *
 * Supports both BLE (Bluetooth Low Energy) and Classic Bluetooth
 * for maximum compatibility with different ESP32 firmware versions.
 */
class BleService : Service() {

    companion object {
        private const val TAG = "BleService"
        const val ACTION_BLE_RX_TEXT = "com.smartglasses.gateway.ACTION_BLE_RX_TEXT"
        const val ACTION_BLE_TX_TEXT = "com.smartglasses.gateway.ACTION_BLE_TX_TEXT"
        const val EXTRA_TEXT = "text"

        // Service UUIDs - must match ESP32 firmware
        private val SERVICE_UUID: UUID = UUID.fromString("4fafc201-1fb5-459e-8fcc-c5c9c331914b")
        private val CHARACTERISTIC_UUID: UUID = UUID.fromString("beb5483e-36e1-4688-b7f5-ea07361b26a8")
        private val CLIENT_CONFIG_UUID: UUID = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")

        // Fallback for Classic Bluetooth
        private val SPP_UUID: UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")

        // Glasses device name patterns
        val DEVICE_NAME_PATTERNS = listOf(
            "Smart Glasses",
            "Nova",
            "ESP32",
            "SmartGlasses"
        )

        // Connection states
        const val STATE_DISCONNECTED = 0
        const val STATE_CONNECTING = 1
        const val STATE_CONNECTED = 2
    }

    // Bluetooth components
    private var bluetoothManager: BluetoothManager? = null
    private var bluetoothAdapter: BluetoothAdapter? = null
    private var bluetoothGatt: BluetoothGatt? = null
    private var bluetoothSocket: BluetoothSocket? = null

    // Connection state
    @Volatile
    private var connectionState = STATE_DISCONNECTED

    // Data queues
    private val outputQueue = ConcurrentLinkedQueue<ByteArray>()
    private var writeThread: Thread? = null

    // Callbacks
    private var connectionCallback: ((Int) -> Unit)? = null
    private var dataCallback: ((ByteArray) -> Unit)? = null

    // Coroutines
    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    // Handler for main thread operations
    private val mainHandler = Handler(Looper.getMainLooper())
    private var receiverRegistered = false

    private val outboundTextReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action != ACTION_BLE_TX_TEXT) return
            val text = intent.getStringExtra(EXTRA_TEXT)?.trim().orEmpty()
            if (text.isEmpty()) return
            sendData(text.toByteArray(Charsets.UTF_8))
        }
    }

    private val gattCallback = object : BluetoothGattCallback() {
        override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
            when (newState) {
                BluetoothProfile.STATE_CONNECTED -> {
                    Log.i(TAG, "BLE Connected to ${gatt.device.name}")
                    connectionState = STATE_CONNECTED
                    connectionCallback?.invoke(STATE_CONNECTED)

                    // Discover services
                    gatt.discoverServices()
                }
                BluetoothProfile.STATE_DISCONNECTED -> {
                    Log.i(TAG, "BLE Disconnected")
                    connectionState = STATE_DISCONNECTED
                    connectionCallback?.invoke(STATE_DISCONNECTED)
                    bluetoothGatt?.close()
                    bluetoothGatt = null
                }
            }
        }

        override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
            if (status == BluetoothGatt.GATT_SUCCESS) {
                Log.i(TAG, "Services discovered")
                // Find our characteristic and enable notifications
                gatt.services.forEach { service ->
                    if (service.uuid == SERVICE_UUID) {
                        service.characteristics.forEach { characteristic ->
                            if (characteristic.uuid == CHARACTERISTIC_UUID) {
                                gatt.setCharacteristicNotification(characteristic, true)
                                val cccd = characteristic.getDescriptor(CLIENT_CONFIG_UUID)
                                if (cccd != null) {
                                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                                        gatt.writeDescriptor(
                                            cccd,
                                            BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                                        )
                                    } else {
                                        @Suppress("DEPRECATION")
                                        run {
                                            cccd.value =
                                                BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                                            gatt.writeDescriptor(cccd)
                                        }
                                    }
                                }
                                sendQueuedData()
                            }
                        }
                    }
                }
            }
        }

        override fun onCharacteristicChanged(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic
        ) {
            if (characteristic.uuid == CHARACTERISTIC_UUID) {
                val data = characteristic.value
                dataCallback?.invoke(data)
            }
        }

        override fun onCharacteristicWrite(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            status: Int
        ) {
            if (status == BluetoothGatt.GATT_SUCCESS) {
                sendQueuedData()
            }
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        initializeBluetooth()
        setDataCallback { data ->
            handleIncomingData(data)
        }
        registerOutboundReceiver()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        autoConnectToKnownDevice()
        return START_STICKY
    }

    override fun onDestroy() {
        unregisterOutboundReceiver()
        disconnect()
        serviceScope.cancel()
        super.onDestroy()
    }

    // ==================== Bluetooth Initialization ====================

    @SuppressLint("MissingPermission")
    private fun initializeBluetooth() {
        bluetoothManager = getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
        bluetoothAdapter = bluetoothManager?.adapter

        if (bluetoothAdapter == null) {
            Log.e(TAG, "Bluetooth not available")
            return
        }

        if (!bluetoothAdapter!!.isEnabled) {
            Log.w(TAG, "Bluetooth is disabled")
            // Don't auto-enable - user must enable manually
        }

        Log.d(TAG, "Bluetooth initialized")
    }

    // ==================== Device Discovery ====================

    @SuppressLint("MissingPermission")
    fun discoverDevices(): List<BluetoothDevice> {
        val adapter = bluetoothAdapter ?: return emptyList()

        // Get paired devices first
        val pairedDevices = adapter.bondedDevices.toList()

        // Filter for glasses devices
        return pairedDevices.filter { device ->
            DEVICE_NAME_PATTERNS.any { pattern ->
                device.name?.contains(pattern, ignoreCase = true) == true
            }
        }
    }

    @SuppressLint("MissingPermission")
    fun startDiscovery(): Boolean {
        return try {
            bluetoothAdapter?.startDiscovery()
            true
        } catch (e: SecurityException) {
            Log.e(TAG, "Discovery permission denied", e)
            false
        }
    }

    // ==================== Connection ====================

    @SuppressLint("MissingPermission")
    fun connect(device: BluetoothDevice): Boolean {
        if (connectionState == STATE_CONNECTING || connectionState == STATE_CONNECTED) {
            Log.w(TAG, "Already connected or connecting")
            return false
        }

        Log.i(TAG, "Connecting to ${device.name}")

        connectionState = STATE_CONNECTING
        connectionCallback?.invoke(STATE_CONNECTING)

        // Try BLE first
        if (device.type == BluetoothDevice.DEVICE_TYPE_LE ||
            Build.VERSION.SDK_INT < Build.VERSION_CODES.S || // Android 11 and below
            checkBluetoothScanPermission()
        ) {
            try {
                bluetoothGatt = device.connectGatt(this, false, gattCallback)
                return true
            } catch (e: SecurityException) {
                Log.e(TAG, "BLE connection permission denied", e)
            }
        }

        // Fallback to Classic Bluetooth (SPP)
        return connectClassic(device)
    }

    private fun connectClassic(device: BluetoothDevice): Boolean {
        try {
            bluetoothSocket = device.createRfcommSocketToServiceRecord(SPP_UUID)
            bluetoothSocket?.connect()

            connectionState = STATE_CONNECTED
            connectionCallback?.invoke(STATE_CONNECTED)

            // Start reading
            startReading()

            // Start writing
            startWriting()

            return true
        } catch (e: IOException) {
            Log.e(TAG, "Classic Bluetooth connection failed", e)
            connectionState = STATE_DISCONNECTED
            connectionCallback?.invoke(STATE_DISCONNECTED)
            return false
        }
    }

    fun disconnect() {
        connectionState = STATE_DISCONNECTED

        try {
            bluetoothGatt?.close()
            bluetoothSocket?.close()
        } catch (e: IOException) {
            Log.e(TAG, "Error closing connection", e)
        }

        bluetoothGatt = null
        bluetoothSocket = null
        writeThread?.interrupt()
        writeThread = null

        connectionCallback?.invoke(STATE_DISCONNECTED)
    }

    // ==================== Data Transmission ====================

    fun sendData(data: ByteArray): Boolean {
        if (connectionState != STATE_CONNECTED) {
            // Queue for later
            outputQueue.offer(data)
            return false
        }

        return try {
            if (bluetoothGatt != null) {
                val characteristic = bluetoothGatt?.getService(SERVICE_UUID)
                    ?.getCharacteristic(CHARACTERISTIC_UUID)
                characteristic?.value = data
                bluetoothGatt?.writeCharacteristic(characteristic)
            } else if (bluetoothSocket != null) {
                bluetoothSocket?.outputStream?.write(data)
                true
            } else {
                outputQueue.offer(data)
                false
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to send data", e)
            false
        }
    }

    private fun sendQueuedData() {
        while (outputQueue.isNotEmpty()) {
            val data = outputQueue.poll() ?: break
            sendData(data)
        }
    }

    private fun startReading() {
        val socket = bluetoothSocket ?: return

        Thread {
            val buffer = ByteArray(1024)
            var bytes: Int

            try {
                val inputStream = socket.inputStream
                while (connectionState == STATE_CONNECTED) {
                    bytes = inputStream.read(buffer)
                    if (bytes > 0) {
                        val data = buffer.copyOf(bytes)
                        mainHandler.post {
                            dataCallback?.invoke(data)
                        }
                    }
                }
            } catch (e: IOException) {
                if (connectionState == STATE_CONNECTED) {
                    Log.e(TAG, "Reading error", e)
                    connectionState = STATE_DISCONNECTED
                    connectionCallback?.invoke(STATE_DISCONNECTED)
                }
            }
        }.start()
    }

    private fun startWriting() {
        writeThread = Thread {
            while (connectionState == STATE_CONNECTED && !Thread.interrupted()) {
                val data = outputQueue.poll() ?: continue

                try {
                    bluetoothSocket?.outputStream?.write(data)
                    Thread.sleep(10) // Small delay between writes
                } catch (e: Exception) {
                    Log.e(TAG, "Write error", e)
                    break
                }
            }
        }.apply { start() }
    }

    // ==================== Permission Checking ====================

    private fun checkBluetoothScanPermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            checkSelfPermission(android.Manifest.permission.BLUETOOTH_SCAN) ==
                android.content.pm.PackageManager.PERMISSION_GRANTED
        } else {
            true
        }
    }

    // ==================== Callbacks ====================

    fun setConnectionCallback(callback: (Int) -> Unit) {
        connectionCallback = callback
    }

    fun setDataCallback(callback: (ByteArray) -> Unit) {
        dataCallback = callback
    }

    fun isConnected(): Boolean = connectionState == STATE_CONNECTED

    fun getConnectionState(): Int = connectionState

    private fun autoConnectToKnownDevice() {
        if (connectionState != STATE_DISCONNECTED) return
        val devices = discoverDevices()
        val device = devices.firstOrNull()
        if (device == null) {
            Log.w(TAG, "No paired Smart Glasses device found")
            return
        }

        connect(device)
    }

    private fun handleIncomingData(data: ByteArray) {
        val text = data.toString(Charsets.UTF_8).trim()
        if (text.isEmpty()) return
        val intent = Intent(ACTION_BLE_RX_TEXT).apply {
            putExtra(EXTRA_TEXT, text)
            `package` = packageName
        }
        sendBroadcast(intent)
        Log.d(TAG, "BLE RX text: $text")
    }

    private fun registerOutboundReceiver() {
        if (receiverRegistered) return
        val filter = IntentFilter(ACTION_BLE_TX_TEXT)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(outboundTextReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            @Suppress("DEPRECATION")
            registerReceiver(outboundTextReceiver, filter)
        }
        receiverRegistered = true
    }

    private fun unregisterOutboundReceiver() {
        if (!receiverRegistered) return
        unregisterReceiver(outboundTextReceiver)
        receiverRegistered = false
    }
}
