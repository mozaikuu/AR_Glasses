import { useCallback, useEffect, useMemo, useState } from "react";
import { useAppStore } from "@/store";
import { initializeServices } from "@/services";

export const useNavigation = () => {
	const { navigationService } = useMemo(() => initializeServices(), []);
	const [isLoading, setIsLoading] = useState(false);

	const isNavigating = useAppStore((state) => state.isNavigating);
	const currentSession = useAppStore((state) => state.navigationSession);
	const destinations = useAppStore((state) => state.destinations);
	const errorMessage = useAppStore((state) => state.navigationError);

	const refreshDestinations = useCallback(async () => {
		setIsLoading(true);
		try {
			await navigationService.getDestinations();
		} finally {
			setIsLoading(false);
		}
	}, [navigationService]);

	const startNavigation = useCallback(
		async (destination: string) => {
			setIsLoading(true);
			try {
				await navigationService.startNavigation(destination);
			} finally {
				setIsLoading(false);
			}
		},
		[navigationService],
	);

	const stopNavigation = useCallback(async () => {
		setIsLoading(true);
		try {
			await navigationService.stopNavigation();
		} finally {
			setIsLoading(false);
		}
	}, [navigationService]);

	const nextStep = useCallback(async () => {
		await navigationService.nextStep();
	}, [navigationService]);

	useEffect(() => {
		refreshDestinations().catch(() => undefined);
	}, [refreshDestinations]);

	return {
		isNavigating,
		currentSession,
		destinations,
		isLoading,
		errorMessage,
		startNavigation,
		stopNavigation,
		nextStep,
		refreshDestinations,
	};
};
