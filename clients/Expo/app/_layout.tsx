import { Stack } from "expo-router";

import "@/global.css";

export default function RootLayout() {
	return (
		<Stack
			screenOptions={{
				headerShown: false,
				animation: "fade",
			}}
		>
			<Stack.Screen name="index" />
			<Stack.Screen name="onboarding" />
			<Stack.Screen name="login" />
			<Stack.Screen name="main" />
		</Stack>
	);
}
