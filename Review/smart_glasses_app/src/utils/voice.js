/**
 * Voice input utilities for Smart Glasses React Native app
 * Handles audio recording and transcription
 */
import { Audio } from 'expo-av';
import { Platform } from 'react-native';

/**
 * Recording status
 */
let recording = null;
let sound = null;
let isRecording = false;

/**
 * Request audio permissions
 * @returns {Promise<boolean>}
 */
export async function requestAudioPermission() {
  if (Platform.OS === 'ios') {
    const { status } = await Audio.requestPermissionsAsync();
    return status === 'granted';
  }
  return true;
}

/**
 * Start voice recording
 * @returns {Promise<boolean>}
 */
export async function startVoiceInput() {
  try {
    // Request permission first
    const hasPermission = await requestAudioPermission();
    if (!hasPermission) {
      throw new Error('Microphone permission not granted');
    }

    // Configure audio mode for recording
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: true,
      playsInSilentModeIOS: true,
    });

    // Create recording
    recording = new Audio.Recording();
    await recording.prepareToRecordAsync(Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY);
    await recording.startAsync();

    isRecording = true;
    console.log('Recording started');
    return true;
  } catch (error) {
    console.error('Failed to start recording:', error);
    return false;
  }
}

/**
 * Stop voice recording and get URI
 * @returns {Promise<string|null>}
 */
export async function stopVoiceInput() {
  try {
    if (!recording) {
      return null;
    }

    await recording.stopAndUnloadAsync();
    const uri = recording.getURI();

    // Reset audio mode
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: false,
      playsInSilentModeIOS: true,
    });

    isRecording = false;
    recording = null;

    console.log('Recording stopped, URI:', uri);
    return uri;
  } catch (error) {
    console.error('Failed to stop recording:', error);
    isRecording = false;
    return null;
  }
}

/**
 * Get recording status
 * @returns {boolean}
 */
export function getIsRecording() {
  return isRecording;
}

/**
 * Transcribe audio using the backend gateway
 * @param {string} audioUri - Local file URI
 * @param {string} gatewayUrl - Gateway URL
 * @returns {Promise<string>}
 */
export async function transcribeAudio(audioUri, gatewayUrl = 'http://localhost:8000') {
  try {
    // For now, we'll send the audio to the gateway for transcription
    // In a real implementation, this would call the backend
    const formData = new FormData();

    if (Platform.OS === 'ios') {
      // iOS file URI needs to be handled differently
      formData.append('audio', {
        uri: audioUri,
        type: 'audio/m4a',
        name: 'recording.m4a',
      });
    } else {
      formData.append('audio', {
        uri: audioUri,
        type: 'audio/3gpp',
        name: 'recording.3gp',
      });
    }

    const response = await fetch(`${gatewayUrl}/process`, {
      method: 'POST',
      body: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    if (!response.ok) {
      throw new Error('Transcription failed');
    }

    const data = await response.json();
    return data.transcription || data.response || '';
  } catch (error) {
    console.error('Transcription error:', error);
    throw error;
  }
}

/**
 * Play audio response from gateway
 * @param {string} audioUrl - URL or path to audio
 * @returns {Promise<void>}
 */
export async function playAudioResponse(audioUrl) {
  try {
    // Unload any previous sound
    if (sound) {
      await sound.unloadAsync();
    }

    // Load and play new sound
    sound = new Audio.Sound();
    await sound.loadAsync({ uri: audioUrl });
    await sound.playAsync();
  } catch (error) {
    console.error('Failed to play audio:', error);
  }
}

/**
 * Stop audio playback
 * @returns {Promise<void>}
 */
export async function stopAudioPlayback() {
  try {
    if (sound) {
      await sound.stopAsync();
      await sound.unloadAsync();
      sound = null;
    }
  } catch (error) {
    console.error('Failed to stop audio:', error);
  }
}

export default {
  requestAudioPermission,
  startVoiceInput,
  stopVoiceInput,
  getIsRecording,
  transcribeAudio,
  playAudioResponse,
  stopAudioPlayback,
};