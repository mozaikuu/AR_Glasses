const { getDefaultConfig } = require("expo/metro-config");
const { withNativewind } = require("nativewind/metro");

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

// Allow bundling textured mesh formats used by temporary building viewers.
if (!config.resolver.assetExts.includes("glb")) {
	config.resolver.assetExts.push("glb", "gltf");
}

module.exports = withNativewind(config);
