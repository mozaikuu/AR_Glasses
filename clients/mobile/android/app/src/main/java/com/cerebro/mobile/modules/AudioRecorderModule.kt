package com.cerebro.mobile.modules

import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import com.facebook.react.bridge.ReadableMap
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.io.IOException

class AudioRecorderModule(private val reactContext: ReactApplicationContext) : ReactContextBaseJavaModule(reactContext) {
	private var recorder: AudioRecord? = null
	private var recordingThread: Thread? = null
	private var isRecording: Boolean = false
	private var tempPcmFile: File? = null
	private var wavFile: File? = null
	private var sampleRate = 16000
	private var channels = 1
	private var bitsPerSample = 16

	override fun getName(): String = "AudioRecorderModule"

	@ReactMethod
	fun startRecording(config: ReadableMap, promise: Promise) {
		if (isRecording) {
			promise.reject("E_RECORDING", "Recording already in progress")
			return
		}

		sampleRate = if (config.hasKey("sampleRate")) config.getInt("sampleRate") else 16000
		channels = if (config.hasKey("channels")) config.getInt("channels") else 1
		bitsPerSample = if (config.hasKey("bitsPerSample")) config.getInt("bitsPerSample") else 16

		val channelConfig = if (channels == 1) AudioFormat.CHANNEL_IN_MONO else AudioFormat.CHANNEL_IN_STEREO
		val audioFormat = AudioFormat.ENCODING_PCM_16BIT
		val bufferSize = AudioRecord.getMinBufferSize(sampleRate, channelConfig, audioFormat)

		if (bufferSize == AudioRecord.ERROR_BAD_VALUE) {
			promise.reject("E_RECORDING", "Invalid audio recorder configuration")
			return
		}

		recorder = AudioRecord(
			MediaRecorder.AudioSource.MIC,
			sampleRate,
			channelConfig,
			audioFormat,
			bufferSize
		)

		tempPcmFile = File(reactContext.cacheDir, "cerebro_recording_${System.currentTimeMillis()}.pcm")
		wavFile = File(reactContext.cacheDir, "cerebro_recording_${System.currentTimeMillis()}.wav")

		try {
			recorder?.startRecording()
		} catch (error: IllegalStateException) {
			promise.reject("E_RECORDING", "Failed to start recording")
			return
		}

		isRecording = true
		recordingThread = Thread {
			writeAudioDataToFile(bufferSize)
		}
		recordingThread?.start()

		promise.resolve(tempPcmFile?.absolutePath)
	}

	@ReactMethod
	fun stopRecording(promise: Promise) {
		if (!isRecording) {
			promise.reject("E_RECORDING", "No recording in progress")
			return
		}

		isRecording = false

		try {
			recorder?.stop()
		} catch (error: IllegalStateException) {
			// ignore
		}
		recorder?.release()
		recorder = null

		try {
			recordingThread?.join(500)
		} catch (error: InterruptedException) {
			// ignore
		}

		val pcmFile = tempPcmFile
		val outputFile = wavFile

		if (pcmFile == null || outputFile == null) {
			promise.reject("E_RECORDING", "Missing recording output")
			return
		}

		try {
			convertPcmToWav(pcmFile, outputFile)
			pcmFile.delete()
			promise.resolve(outputFile.absolutePath)
		} catch (error: IOException) {
			promise.reject("E_RECORDING", "Failed to finalize WAV")
		}
	}

	private fun writeAudioDataToFile(bufferSize: Int) {
		val buffer = ByteArray(bufferSize)
		val file = tempPcmFile ?: return
		var outputStream: FileOutputStream? = null

		try {
			outputStream = FileOutputStream(file)
			while (isRecording) {
				val read = recorder?.read(buffer, 0, buffer.size) ?: 0
				if (read > 0) {
					outputStream.write(buffer, 0, read)
				}
			}
		} catch (error: IOException) {
			// ignore
		} finally {
			try {
				outputStream?.close()
			} catch (error: IOException) {
				// ignore
			}
		}
	}

	@Throws(IOException::class)
	private fun convertPcmToWav(pcmFile: File, wavFile: File) {
		val pcmSize = pcmFile.length().toInt()
		val totalDataLen = pcmSize + 36
		val byteRate = sampleRate * channels * bitsPerSample / 8

		val header = ByteArray(44)
		header[0] = 'R'.code.toByte()
		header[1] = 'I'.code.toByte()
		header[2] = 'F'.code.toByte()
		header[3] = 'F'.code.toByte()
		writeInt(header, 4, totalDataLen)
		header[8] = 'W'.code.toByte()
		header[9] = 'A'.code.toByte()
		header[10] = 'V'.code.toByte()
		header[11] = 'E'.code.toByte()
		header[12] = 'f'.code.toByte()
		header[13] = 'm'.code.toByte()
		header[14] = 't'.code.toByte()
		header[15] = ' '.code.toByte()
		writeInt(header, 16, 16)
		writeShort(header, 20, 1.toShort())
		writeShort(header, 22, channels.toShort())
		writeInt(header, 24, sampleRate)
		writeInt(header, 28, byteRate)
		writeShort(header, 32, (channels * bitsPerSample / 8).toShort())
		writeShort(header, 34, bitsPerSample.toShort())
		header[36] = 'd'.code.toByte()
		header[37] = 'a'.code.toByte()
		header[38] = 't'.code.toByte()
		header[39] = 'a'.code.toByte()
		writeInt(header, 40, pcmSize)

		FileInputStream(pcmFile).use { inputStream ->
			FileOutputStream(wavFile).use { outputStream ->
				outputStream.write(header, 0, 44)
				val buffer = ByteArray(1024)
				var read: Int
				while (inputStream.read(buffer).also { read = it } != -1) {
					outputStream.write(buffer, 0, read)
				}
			}
		}
	}

	private fun writeInt(buffer: ByteArray, offset: Int, value: Int) {
		buffer[offset] = (value and 0xff).toByte()
		buffer[offset + 1] = (value shr 8 and 0xff).toByte()
		buffer[offset + 2] = (value shr 16 and 0xff).toByte()
		buffer[offset + 3] = (value shr 24 and 0xff).toByte()
	}

	private fun writeShort(buffer: ByteArray, offset: Int, value: Short) {
		buffer[offset] = (value.toInt() and 0xff).toByte()
		buffer[offset + 1] = (value.toInt() shr 8 and 0xff).toByte()
	}
}
