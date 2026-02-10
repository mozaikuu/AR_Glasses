import Foundation
import AVFoundation
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

    // State
    private(set) var isRecording = false

    // Queue for audio data
    private var audioDataQueue = DispatchQueue(label: "com.smartglasses.audioqueue")
    private var isProcessing = false

    // MARK: - Initialization

    override init() {
        super.init()
        setupAudioSession()
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
        // Handle WebSocket events
    }

    func didReceive(message: String, client: WebSocketClient) {
        // Handle text message
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
