import RNFS from "react-native-fs";

export const isRNFSAvailable = Boolean(RNFS?.DocumentDirectoryPath);

export default RNFS;
