import type { Config } from "tailwindcss";

const config: Config = {
	content: [
		"./app/**/*.{js,ts,jsx,tsx,mdx}",
		"./components/**/*.{js,ts,jsx,tsx,mdx}",
		"./lib/**/*.{js,ts,jsx,tsx,mdx}",
	],
	theme: {
		extend: {
			fontFamily: {
				display: ["var(--font-display)", "sans-serif"],
				arabic: ["var(--font-arabic)", "sans-serif"],
			},
			colors: {
				dusk: {
					950: "#05090f",
					900: "#091321",
					800: "#102033",
				},
				mint: {
					300: "#6ee7c9",
					500: "#2dd4bf",
					700: "#0f766e",
				},
				amber: {
					300: "#fcd48a",
					500: "#f59e0b",
					700: "#b45309",
				},
			},
			boxShadow: {
				glow: "0 12px 36px rgba(45, 212, 191, 0.25)",
				panel: "0 18px 50px rgba(6, 20, 35, 0.32)",
			},
		},
	},
	plugins: [],
};

export default config;
