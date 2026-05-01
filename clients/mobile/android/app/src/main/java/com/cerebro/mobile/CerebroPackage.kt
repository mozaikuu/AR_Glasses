package com.cerebro.mobile

import com.cerebro.mobile.modules.AudioPlayerModule
import com.cerebro.mobile.modules.AudioRecorderModule
import com.cerebro.mobile.modules.CameraModule
import com.facebook.react.ReactPackage
import com.facebook.react.bridge.NativeModule
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.uimanager.ViewManager

class CerebroPackage : ReactPackage {
	override fun createNativeModules(reactContext: ReactApplicationContext): List<NativeModule> {
		return listOf(
			AudioRecorderModule(reactContext),
			CameraModule(reactContext),
			AudioPlayerModule(reactContext)
		)
	}

	override fun createViewManagers(reactContext: ReactApplicationContext): List<ViewManager<*, *>> {
		return emptyList()
	}
}
