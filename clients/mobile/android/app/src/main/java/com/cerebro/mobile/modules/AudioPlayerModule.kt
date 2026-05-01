package com.cerebro.mobile.modules

import android.media.MediaPlayer
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod

class AudioPlayerModule(reactContext: ReactApplicationContext) : ReactContextBaseJavaModule(reactContext) {
	private var mediaPlayer: MediaPlayer? = null

	override fun getName(): String = "AudioPlayerModule"

	@ReactMethod
	fun playAudio(filePath: String, promise: Promise) {
		try {
			stopAndRelease()
			mediaPlayer = MediaPlayer().apply {
				setDataSource(filePath)
				setOnCompletionListener {
					stopAndRelease()
				}
				prepare()
				start()
			}
			promise.resolve(null)
		} catch (error: Exception) {
			promise.reject("E_AUDIO", "Failed to play audio")
		}
	}

	@ReactMethod
	fun stopAudio(promise: Promise) {
		stopAndRelease()
		promise.resolve(null)
	}

	@ReactMethod
	fun isPlaying(promise: Promise) {
		promise.resolve(mediaPlayer?.isPlaying == true)
	}

	@ReactMethod
	fun getDuration(promise: Promise) {
		promise.resolve(mediaPlayer?.duration ?: 0)
	}

	private fun stopAndRelease() {
		try {
			mediaPlayer?.stop()
		} catch (error: Exception) {
			// ignore
		}
		mediaPlayer?.release()
		mediaPlayer = null
	}
}
