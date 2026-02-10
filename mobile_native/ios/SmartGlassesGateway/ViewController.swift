import UIKit
import AVFoundation

class ViewController: UIViewController {

    // MARK: - UI Components

    private lazy var statusLabel: UILabel = {
        let label = UILabel()
        label.text = "Status: Ready"
        label.textAlignment = .center
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()

    private lazy var startButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("Start Recording", for: .normal)
        button.titleLabel?.font = UIFont.boldSystemFont(ofSize: 18)
        button.translatesAutoresizingMaskIntoConstraints = false
        button.addTarget(self, action: #selector(startRecording), for: .touchUpInside)
        return button
    }()

    private lazy var stopButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("Stop Recording", for: .normal)
        button.titleLabel?.font = UIFont.boldSystemFont(ofSize: 18)
        button.isEnabled = false
        button.translatesAutoresizingMaskIntoConstraints = false
        button.addTarget(self, action: #selector(stopRecording), for: .touchUpInside)
        return button
    }()

    private lazy var activityIndicator: UIActivityIndicatorView = {
        let indicator = UIActivityIndicatorView(style: .medium)
        indicator.translatesAutoresizingMaskIntoConstraints = false
        indicator.hidesWhenStopped = true
        return indicator
    }()

    // MARK: - Properties

    private var audioManager: AudioManager?
    private let serverURL = "wss://YOUR_SERVER_IP:8765"

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        initializeAudioManager()
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        // Note: On iOS, audio stops when app goes to background
        // unless UIBackgroundModes: audio is configured
    }

    // MARK: - UI Setup

    private func setupUI() {
        view.backgroundColor = .systemBackground

        view.addSubview(statusLabel)
        view.addSubview(startButton)
        view.addSubview(stopButton)
        view.addSubview(activityIndicator)

        NSLayoutConstraint.activate([
            statusLabel.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            statusLabel.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 40),

            startButton.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            startButton.centerYAnchor.constraint(equalTo: view.centerYAnchor),
            startButton.widthAnchor.constraint(equalToConstant: 200),
            startButton.heightAnchor.constraint(equalToConstant: 50),

            stopButton.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            stopButton.topAnchor.constraint(equalTo: startButton.bottomAnchor, constant: 20),
            stopButton.widthAnchor.constraint(equalToConstant: 200),
            stopButton.heightAnchor.constraint(equalToConstant: 50),

            activityIndicator.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            activityIndicator.topAnchor.constraint(equalTo: stopButton.bottomAnchor, constant: 20)
        ])
    }

    private func initializeAudioManager() {
        audioManager = AudioManager()
        audioManager?.delegate = self
        audioManager?.onStatusChange = { [weak self] isRecording in
            DispatchQueue.main.async {
                self?.updateUI(isRecording: isRecording)
            }
        }
    }

    private func updateUI(isRecording: Bool) {
        statusLabel.text = isRecording ? "Status: Recording..." : "Status: Stopped"
        startButton.isEnabled = !isRecording
        stopButton.isEnabled = isRecording

        if isRecording {
            activityIndicator.startAnimating()
        } else {
            activityIndicator.stopAnimating()
        }
    }

    // MARK: - Actions

    @objc private func startRecording() {
        guard checkPermissions() else {
            requestPermissions()
            return
        }

        statusLabel.text = "Status: Connecting..."

        audioManager?.connectAndStart(url: serverURL) { [weak self] success, error in
            DispatchQueue.main.async {
                if success {
                    self?.updateUI(isRecording: true)
                    self?.statusLabel.text = "Status: Recording & Connected"
                } else {
                    self?.statusLabel.text = "Status: Connection failed - \(error ?? "unknown")"
                }
            }
        }
    }

    @objc private func stopRecording() {
        audioManager?.stop()
        updateUI(isRecording: false)
        statusLabel.text = "Status: Stopped"
    }

    // MARK: - Permissions

    private func checkPermissions() -> Bool {
        return AVAudioSession.sharedInstance().recordPermission == .granted
    }

    private func requestPermissions() {
        AVAudioSession.sharedInstance().requestRecordPermission { granted in
            DispatchQueue.main.async {
                if granted {
                    self.statusLabel.text = "Status: Permission granted"
                } else {
                    self.statusLabel.text = "Status: Permission denied - Enable in Settings"
                }
            }
        }
    }
}

// MARK: - AudioManagerDelegate

extension ViewController: AudioManagerDelegate {
    func audioManager(_ manager: AudioManager, didReceiveText text: String) {
        // Handle text response from server
        DispatchQueue.main.async {
            self.statusLabel.text = "Status: Response received"
        }
    }

    func audioManager(_ manager: AudioManager, didFailWithError error: Error) {
        DispatchQueue.main.async {
            self.statusLabel.text = "Status: Error - \(error.localizedDescription)"
            self.updateUI(isRecording: false)
        }
    }
}
