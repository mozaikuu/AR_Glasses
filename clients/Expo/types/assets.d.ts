declare module "*.glb" {
	const asset: number;
	export default asset;
}

declare module "*.gltf" {
	const asset: number;
	export default asset;
}

declare module "*.json" {
	const value: unknown;
	export default value;
}
