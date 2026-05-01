import React, { useEffect } from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";
import AssistantScreen from "@/screens/AssistantScreen";
import NavigationScreen from "@/screens/NavigationScreen";
import SettingsScreen from "@/screens/SettingsScreen";
import { initializeServices } from "@/services";

const Tab = createBottomTabNavigator();

const App = () => {
	useEffect(() => {
		initializeServices();
	}, []);

	return (
		<GestureHandlerRootView style={{ flex: 1 }}>
			<SafeAreaProvider>
				<NavigationContainer>
					<Tab.Navigator screenOptions={{ headerShown: false }}>
						<Tab.Screen name="Assistant" component={AssistantScreen} />
						<Tab.Screen name="Navigation" component={NavigationScreen} />
						<Tab.Screen name="Settings" component={SettingsScreen} />
					</Tab.Navigator>
				</NavigationContainer>
			</SafeAreaProvider>
		</GestureHandlerRootView>
	);
};

export default App;
