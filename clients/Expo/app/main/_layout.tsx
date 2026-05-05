import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

import "@/global.css";

export default function MainTabsLayout() {
	return (
		<Tabs
			screenOptions={{
				headerShown: false,
				tabBarActiveTintColor: "#007AFF",
			}}
		>
			<Tabs.Screen
				name="index"
				options={{
					title: "Home",
					tabBarIcon: ({ color, size }) => (
						<Ionicons name="home" size={size} color={color} />
					),
				}}
			/>
			<Tabs.Screen
				name="bus"
				options={{
					title: "Bus",
					tabBarIcon: ({ color, size }) => (
						<Ionicons name="bus" size={size} color={color} />
					),
				}}
			/>
			<Tabs.Screen
				name="indoornav"
				options={{
					title: "Indoor Nav",
					tabBarIcon: ({ color, size }) => (
						<Ionicons name="navigate" size={size} color={color} />
					),
				}}
			/>
			<Tabs.Screen
				name="navigation"
				options={{
					title: "Navigation",
					tabBarIcon: ({ color, size }) => (
						<Ionicons name="map" size={size} color={color} />
					),
				}}
			/>
			<Tabs.Screen
				name="companion"
				options={{
					title: "Companion",
					tabBarIcon: ({ color, size }) => (
						<Ionicons name="person" size={size} color={color} />
					),
				}}
			/>
		</Tabs>
	);
}
