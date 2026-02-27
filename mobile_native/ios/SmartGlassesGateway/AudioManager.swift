import Foundation
import AVFoundation
import CoreBluetooth
import Starscream

/**
 * Protocol for AudioManager delegate callbacks.
 */
protocol AudioManagerDelegate: AnyObject {
    func audioManager(_ manager: AudioManager, didReceiveText text: String)
    func audioManager(_ manager: AudioManager, didFailWithError error: Error)
}

/**
 * Audio capture and WebSocket streaming manager for iOS.
 *
 * Limitations on iOS:
 * - Background audio requires UIBackgroundModes: audio entitlement
 * - iOS may suspend app after ~10 minutes of background audio
 * - Must show recording indicator in status bar
 */
class AudioManager: NSObject {

    // MARK: - Properties

    weak var delegate: AudioManagerDelegate?
    var onStatusChange: ((Bool) -> Void)?

    // Audio configuration
    private let sampleRate = 16000
    private let bufferDuration: TimeInterval = 1.0

    // Audio components
    private var audioRecorder: AVAudioRecorder?
    private var audioPlayer: AVAudioPlayer?
    private var recordingURL: URL?

    // WebSocket
    private var webSocket: WebSocket?
    private var isConnected = false
    private var serverURL = ""

    // BLE bridge
    private var centralManager: CBCentralManager?
    private var glassesPeripheral: CBPeripheral?
    private var glassesCharacteristic: CBCharacteristic?

    private let serviceUUID = CBUUID(string: "4fafc201-1fb5-459e-8fcc-c5c9c331914b")
    private let characteristicUUID = CBUUID(string: "beb5483e-36e1-4688-b7f5-ea07361b26a8")
    private let namePatterns = ["smart glasses", "nova", "esp32", "smartglasses"]

    // State
    private(set) var isRecording = false

    // Queue for audio data
    private var audioDataQueue = DispatchQueue(label: "com.smartglasses.audioqueue")
    private var isProcessing = false

    // MARK: - Initialization

    override init() {
        super.init()
        setupAudioSession()
        centralManager = CBCentralManager(delegate: self, queue: nil)
    }

    deinit {
        stop()
    }

    // MARK: - Audio Session Setup

    private func setupAudioSession() {
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playAndRecord,
                                   mode: .default,
                                   options: [.defaultToSpeaker, .allowBluetooth])
            try session.setActive(true)
        } catch {
            print("Failed to setup audio session: \(error)")
        }
    }

    // MARK: - Recording Setup

    private func setupRecorder() throws {
        // Create temporary file for recording
        let tempDir = FileManager.default.temporaryDirectory
        recordingURL = tempDir.appendingPathComponent("recording_\(UUID().uuidString).caf")

        // Recording settings for 16kHz mono PCM
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatLinearPCM),
            AVSampleRateKey: sampleRate,
            AVNumberOfChannelsKey: 1,
            AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false,
            AVLinearPCMIsBigEndianKey: false,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]

        audioRecorder = try AVAudioRecorder(url: recordingURL!, settings: settings)
        audioRecorder?.delegate = self
        audioRecorder?.isMeteringEnabled = true
        audioRecorder?.prepareToRecord()
    }

    // MARK: - Public Methods

    func connectAndStart(url: String, completion: @escaping (Bool, String?) -> Void) {
        serverURL = url

        do {
            try setupRecorder()
        } catch {
            completion(false, "Failed to setup recorder: \(error.localizedDescription)")
            return
        }

        // Connect WebSocket
        guard let url = URL(string: url) else {
            completion(false, "Invalid URL")
            return
        }

        var request = URLRequest(url: url)
        request.timeoutInterval = 10
        request.setValue("ios", forHTTPHeaderField: "X-Device-Type")
        request.setValue("1.0.0", forHTTPHeaderField: "X-App-Version")

        webSocket = WebSocket(request: request)
        webSocket?.delegate = self
        webSocket?.connect()

        // Start recording after a short delay to allow WebSocket connection
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) { [weak self] in
            self?.startRecording()
            completion(true, nil)
        }
    }

    func startRecording() {
        guard !isRecording else { return }

        do {
            try AVAudioSession.sharedInstance().setActive(true)
            audioRecorder?.record(forDuration: bufferDuration)
            isRecording = true
            onStatusChange?(true)
            processAudioQueue()
        } catch {
            print("Failed to start recording: \(error)")
        }
    }

    func stop() {
        isRecording = false
        audioRecorder?.stop()
        webSocket?.disconnect()
        isConnected = false
        onStatusChange?(false)
        if let peripheral = glassesPeripheral {
            centralManager?.cancelPeripheralConnection(peripheral)
        }

        // Clean up temp file
        if let url = recordingURL {
            try? FileManager.default.removeItem(at: url)
        }
    }

    // MARK: - Audio Processing

    private func processAudioQueue() {
        guard isRecording else { return }

        audioDataQueue.async { [weak self] in
            self?.processAudioData()
        }
    }

    private func processAudioData() {
        guard isRecording, let url = recordingURL else { return }

        do {
            let audioData = try Data(contentsOf: url)
            if audioData.count > 0 && isConnected {
                webSocket?.write(data: audioData)
            }

            // Schedule next processing
            DispatchQueue.main.asyncAfter(deadline: .now() + bufferDuration) { [weak self] in
                self?.processAudioQueue()
            }
        } catch {
            print("Failed to read audio data: \(error)")
        }
    }

    // MARK: - Playback

    func playAudio(data: Data) {
        do {
            audioPlayer = try AVAudioPlayer(data: data)
            audioPlayer?.prepareToPlay()
            audioPlayer?.play()
        } catch {
            print("Failed to play audio: \(error)")
        }
    }
}

// MARK: - AVAudioRecorderDelegate

extension AudioManager: AVAudioRecorderDelegate {
    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        if flag && isRecording {
            // Restart recording for continuous capture
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { [weak self] in
                self?.audioRecorder?.record()
            }
        }
    }

    func audioRecorderEncodeErrorDidOccur(_ recorder: AVAudioRecorder, error: Error?) {
        if let error = error {
            delegate?.audioManager(self, didFailWithError: error)
        }
    }
}

// MARK: - WebSocketDelegate

extension AudioManager: WebSocketDelegate {
    func didReceive(event: WebSocketEvent, client: WebSocketClient) {
        switch event {
        case .connected:
            isConnected = true
            print("WebSocket connected")
        case .disconnected(let reason, _):
            isConnected = false
            print("WebSocket disconnected: \(reason)")
            DispatchQueue.main.asyncAfter(deadline: .now() + 5.0) { [weak self] in
                self?.webSocket?.connect()
            }
        case .text(let message):
            routeServerTextToBLE(message)
            delegate?.audioManager(self, didReceiveText: message)
        case .binary(let data):
            playAudio(data: data)
        case .error(let error):
            isConnected = false
            if let error {
                delegate?.audioManager(self, didFailWithError: error)
            }
        default:
            break
        }
    }

    func didReceive(message: String, client: WebSocketClient) {
        routeServerTextToBLE(message)
        delegate?.audioManager(self, didReceiveText: message)
    }

    func didReceive(data: Data, client: WebSocketClient) {
        // Handle binary message (audio response)
        playAudio(data: data)
    }

    func didConnect(client: WebSocketClient) {
        isConnected = true
        print("WebSocket connected")
    }

    func didDisconnect(client: WebSocketClient, error: Error?) {
        isConnected = false
        if let error = error {
            print("WebSocket disconnected: \(error)")
            delegate?.audioManager(self, didFailWithError: error)
        }

        // Attempt reconnection (limited)
        DispatchQueue.main.asyncAfter(deadline: .now() + 5.0) { [weak self] in
            self?.webSocket?.connect()
        }
    }
}

// MARK: - BLE Bridge

extension AudioManager: CBCentralManagerDelegate, CBPeripheralDelegate {
    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        if central.state == .poweredOn {
            startBLEScan()
        }
    }

    private func startBLEScan() {
        centralManager?.scanForPeripherals(withServices: [serviceUUID], options: nil)
    }

    func centralManager(
        _ central: CBCentralManager,
        didDiscover peripheral: CBPeripheral,
        advertisementData: [String: Any],
        rssi RSSI: NSNumber
    ) {
        let name = (peripheral.name ?? "").lowercased()
        let matches = namePatterns.contains { name.contains($0) }
        guard matches else { return }

        central.stopScan()
        glassesPeripheral = peripheral
        peripheral.delegate = self
        central.connect(peripheral, options: nil)
    }

    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        peripheral.discoverServices([serviceUUID])
    }

    func centralManager(
        _ central: CBCentralManager,
        didDisconnectPeripheral peripheral: CBPeripheral,
        error: Error?
    ) {
        glassesCharacteristic = nil
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) { [weak self] in
            self?.startBLEScan()
        }
    }

    func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        guard error == nil, let services = peripheral.services else { return }
        for service in services where service.uuid == serviceUUID {
            peripheral.discoverCharacteristics([characteristicUUID], for: service)
        }
    }

    func peripheral(
        _ peripheral: CBPeripheral,
        didDiscoverCharacteristicsFor service: CBService,
        error: Error?
    ) {
        guard error == nil, let characteristics = service.characteristics else { return }
        for characteristic in characteristics where characteristic.uuid == characteristicUUID {
            glassesCharacteristic = characteristic
            peripheral.setNotifyValue(true, for: characteristic)
        }
    }

    func peripheral(
        _ peripheral: CBPeripheral,
        didUpdateValueFor characteristic: CBCharacteristic,
        error: Error?
    ) {
        guard error == nil,
              characteristic.uuid == characteristicUUID,
              let data = characteristic.value,
              let text = String(data: data, encoding: .utf8)?
                .trimmingCharacters(in: .whitespacesAndNewlines),
              !text.isEmpty else { return }

        if text.hasPrefix("CMD:") {
            let commandText = String(text.dropFirst(4)).trimmingCharacters(in: .whitespacesAndNewlines)
            if !commandText.isEmpty {
                sendTextCommandToServer(commandText)
            }
        }
    }

    private func sendTextCommandToServer(_ command: String) {
        guard isConnected else { return }
        let payload: [String: String] = [
            "type": "text_command",
            "text": command,
            "source": "ble_esp32_ios"
        ]

        guard let data = try? JSONSerialization.data(withJSONObject: payload),
              let json = String(data: data, encoding: .utf8) else {
            return
        }

        webSocket?.write(string: json)
    }

    private func routeServerTextToBLE(_ message: String) {
        guard let data = message.data(using: .utf8),
              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return
        }

        let type = (obj["type"] as? String ?? "").lowercased()
        guard type == "response" || type == "text" || type == "command",
              let responseText = (obj["text"] as? String)?
                .trimmingCharacters(in: .whitespacesAndNewlines),
              !responseText.isEmpty else {
            return
        }

        sendTextToBLE("TTS:\(String(responseText.prefix(180)))")
    }

    private func sendTextToBLE(_ text: String) {
        guard let peripheral = glassesPeripheral,
              let characteristic = glassesCharacteristic else {
            return
        }

        guard let data = text.data(using: .utf8) else { return }
        peripheral.writeValue(data, for: characteristic, type: .withResponse)
    }
}
