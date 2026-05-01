package com.cerebro.mobile.modules

import android.app.Activity
import android.content.Intent
import android.graphics.BitmapFactory
import android.provider.MediaStore
import androidx.core.content.FileProvider
import com.facebook.react.bridge.ActivityEventListener
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import com.facebook.react.bridge.ReadableMap
import java.io.File
import java.io.FileOutputStream

class CameraModule(private val reactContext: ReactApplicationContext) : ReactContextBaseJavaModule(reactContext), ActivityEventListener {
	private var pendingPromise: Promise? = null
	private var pendingFile: File? = null
	private var pendingQuality: Int = 85

	companion object {
		private const val REQUEST_CODE = 8701
	}

	init {
		reactContext.addActivityEventListener(this)
	}

	override fun getName(): String = "CameraModule"

	@ReactMethod
	fun capturePhoto(options: ReadableMap, promise: Promise) {
		if (pendingPromise != null) {
			promise.reject("E_CAMERA_BUSY", "Camera capture already in progress")
			return
		}

		val activity = currentActivity
		if (activity == null) {
			promise.reject("E_NO_ACTIVITY", "No active Activity")
			return
		}

		val intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
		if (intent.resolveActivity(activity.packageManager) == null) {
			promise.reject("E_NO_CAMERA", "No camera application available")
			return
		}

		val quality = if (options.hasKey("quality")) (options.getDouble("quality") * 100).toInt() else 85
		pendingQuality = quality.coerceIn(30, 100)

		val file = File(reactContext.cacheDir, "cerebro_photo_${System.currentTimeMillis()}.jpg")
		val photoUri = FileProvider.getUriForFile(activity, activity.packageName + ".fileprovider", file)
		intent.putExtra(MediaStore.EXTRA_OUTPUT, photoUri)
		intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)

		pendingPromise = promise
		pendingFile = file
		activity.startActivityForResult(intent, REQUEST_CODE)
	}

	@ReactMethod
	fun startPreview(promise: Promise) {
		promise.resolve(null)
	}

	@ReactMethod
	fun stopPreview(promise: Promise) {
		promise.resolve(null)
	}

	override fun onActivityResult(activity: Activity?, requestCode: Int, resultCode: Int, data: Intent?) {
		if (requestCode != REQUEST_CODE) {
			return
		}

		val promise = pendingPromise
		val file = pendingFile
		pendingPromise = null
		pendingFile = null

		if (promise == null || file == null) {
			return
		}

		if (resultCode != Activity.RESULT_OK) {
			promise.reject("E_CAMERA_CANCELLED", "Camera capture cancelled")
			return
		}

		try {
			val bitmap = BitmapFactory.decodeFile(file.absolutePath)
			if (bitmap == null) {
				promise.reject("E_CAMERA", "Failed to decode camera image")
				return
			}
			FileOutputStream(file).use { outputStream ->
				bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG, pendingQuality, outputStream)
			}
			bitmap.recycle()
			promise.resolve(file.absolutePath)
		} catch (error: Exception) {
			promise.reject("E_CAMERA", "Failed to process camera image")
		}
	}

	override fun onNewIntent(intent: Intent?) {
		// No-op
	}
}
