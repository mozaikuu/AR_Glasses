import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ScrollView,
} from 'react-native';
import { useSelector } from 'react-redux';
import { Ionicons } from '@expo/vector-icons';
import { lightTheme, darkTheme } from '../constants/theme';

const VRScreen = () => {
  const isDarkMode = useSelector((state) => state.theme.isDarkMode);
  const devices = useSelector((state) => state.devices.devices);
  const theme = isDarkMode ? darkTheme : lightTheme;

  const [vrActive, setVrActive] = useState(false);
  const [vrMode, setVrMode] = useState('desktop'); // desktop, mobile, quest

  const handleStartVR = () => {
    Alert.alert(
      'VR Experience',
      'VR functionality would be implemented here using:\n\n- Meta Quest SDK\n- WebXR API\n- react-native-vr or expo-gl\n\nThis would provide an immersive virtual reality experience for controlling your smart home.',
      [{ text: 'OK' }]
    );
    setVrActive(true);
  };

  const handleStopVR = () => {
    setVrActive(false);
  };

  const handleModeSelect = (mode) => {
    setVrMode(mode);
    Alert.alert(
      'VR Mode Selected',
      `Selected ${mode} mode. In a full implementation, this would configure the VR experience for ${mode === 'quest' ? 'Meta Quest headset' : mode === 'mobile' ? 'mobile VR (Cardboard/Daydream)' : 'desktop VR'}.`,
      [{ text: 'OK' }]
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {!vrActive ? (
        <ScrollView
          style={styles.setupContainer}
          contentContainerStyle={styles.setupContent}
        >
          <View style={styles.header}>
            <Ionicons name="glasses" size={64} color={theme.primary} />
            <Text style={[styles.title, { color: theme.text }]}>
              Virtual Reality
            </Text>
            <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
              Immersive VR control for your smart home
            </Text>
          </View>

          <View style={styles.infoCard}>
            <View style={styles.infoRow}>
              <Ionicons name="information-circle" size={24} color={theme.info} />
              <View style={styles.infoContent}>
                <Text style={[styles.infoTitle, { color: theme.text }]}>
                  VR Features
                </Text>
                <Text style={[styles.infoText, { color: theme.textSecondary }]}>
                  • Immersive 3D home visualization{'\n'}
                  • Hand tracking and gestures{'\n'}
                  • Voice commands{'\n'}
                  • Multi-device control{'\n'}
                  • Meta Quest support
                </Text>
              </View>
            </View>
          </View>

          <View style={styles.modeSection}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>
              VR Mode
            </Text>
            <View style={styles.modeOptions}>
              <TouchableOpacity
                style={[
                  styles.modeCard,
                  {
                    backgroundColor:
                      vrMode === 'quest' ? theme.primary : theme.card,
                    borderColor: theme.border,
                  },
                ]}
                onPress={() => handleModeSelect('quest')}
              >
                <Ionicons
                  name="glasses"
                  size={32}
                  color={vrMode === 'quest' ? '#FFFFFF' : theme.primary}
                />
                <Text
                  style={[
                    styles.modeTitle,
                    { color: vrMode === 'quest' ? '#FFFFFF' : theme.text },
                  ]}
                >
                  Meta Quest
                </Text>
                <Text
                  style={[
                    styles.modeDescription,
                    {
                      color: vrMode === 'quest' ? '#FFFFFF' : theme.textSecondary,
                    },
                  ]}
                >
                  Full VR headset experience
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.modeCard,
                  {
                    backgroundColor:
                      vrMode === 'mobile' ? theme.primary : theme.card,
                    borderColor: theme.border,
                  },
                ]}
                onPress={() => handleModeSelect('mobile')}
              >
                <Ionicons
                  name="phone-portrait"
                  size={32}
                  color={vrMode === 'mobile' ? '#FFFFFF' : theme.primary}
                />
                <Text
                  style={[
                    styles.modeTitle,
                    { color: vrMode === 'mobile' ? '#FFFFFF' : theme.text },
                  ]}
                >
                  Mobile VR
                </Text>
                <Text
                  style={[
                    styles.modeDescription,
                    {
                      color: vrMode === 'mobile' ? '#FFFFFF' : theme.textSecondary,
                    },
                  ]}
                >
                  Cardboard/Daydream
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.modeCard,
                  {
                    backgroundColor:
                      vrMode === 'desktop' ? theme.primary : theme.card,
                    borderColor: theme.border,
                  },
                ]}
                onPress={() => handleModeSelect('desktop')}
              >
                <Ionicons
                  name="desktop"
                  size={32}
                  color={vrMode === 'desktop' ? '#FFFFFF' : theme.primary}
                />
                <Text
                  style={[
                    styles.modeTitle,
                    { color: vrMode === 'desktop' ? '#FFFFFF' : theme.text },
                  ]}
                >
                  Desktop VR
                </Text>
                <Text
                  style={[
                    styles.modeDescription,
                    {
                      color: vrMode === 'desktop' ? '#FFFFFF' : theme.textSecondary,
                    },
                  ]}
                >
                  WebXR compatible
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          {devices.length > 0 && (
            <View style={styles.statsCard}>
              <Text style={[styles.statsTitle, { color: theme.text }]}>
                Your Smart Home
              </Text>
              <View style={styles.statsRow}>
                <View style={styles.statItem}>
                  <Text style={[styles.statValue, { color: theme.primary }]}>
                    {devices.length}
                  </Text>
                  <Text style={[styles.statLabel, { color: theme.textSecondary }]}>
                    Devices
                  </Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={[styles.statValue, { color: theme.success }]}>
                    {devices.filter((d) => d.state === 'ON' || d.state === 'RUNNING').length}
                  </Text>
                  <Text style={[styles.statLabel, { color: theme.textSecondary }]}>
                    Active
                  </Text>
                </View>
              </View>
            </View>
          )}

          <TouchableOpacity
            style={[styles.startButton, { backgroundColor: theme.primary }]}
            onPress={handleStartVR}
          >
            <Ionicons name="glasses" size={24} color="#FFFFFF" />
            <Text style={styles.startButtonText}>Start VR Experience</Text>
          </TouchableOpacity>

          <View style={styles.noteCard}>
            <Ionicons name="warning" size={20} color={theme.warning} />
            <Text style={[styles.noteText, { color: theme.textSecondary }]}>
              VR functionality requires compatible hardware. Meta Quest support
              would require the Meta Quest SDK. This is a placeholder
              implementation.
            </Text>
          </View>
        </ScrollView>
      ) : (
        <View style={styles.vrViewContainer}>
          <View style={styles.vrView}>
            <View style={styles.vrPlaceholder}>
              <Ionicons name="glasses-outline" size={80} color={theme.textSecondary} />
              <Text style={[styles.vrPlaceholderText, { color: theme.textSecondary }]}>
                VR View
              </Text>
              <Text style={[styles.vrPlaceholderSubtext, { color: theme.textSecondary }]}>
                {vrMode === 'quest'
                  ? 'Meta Quest VR environment would appear here'
                  : vrMode === 'mobile'
                  ? 'Mobile VR view would appear here'
                  : 'Desktop VR view would appear here'}
              </Text>
              <View style={styles.vrControls}>
                <View style={styles.vrControlHint}>
                  <Ionicons name="hand-left" size={24} color={theme.textSecondary} />
                  <Text style={[styles.vrControlText, { color: theme.textSecondary }]}>
                    Hand Tracking
                  </Text>
                </View>
                <View style={styles.vrControlHint}>
                  <Ionicons name="mic" size={24} color={theme.textSecondary} />
                  <Text style={[styles.vrControlText, { color: theme.textSecondary }]}>
                    Voice Commands
                  </Text>
                </View>
              </View>
            </View>

            <TouchableOpacity
              style={[styles.stopButton, { backgroundColor: theme.error }]}
              onPress={handleStopVR}
            >
              <Ionicons name="close" size={24} color="#FFFFFF" />
              <Text style={styles.stopButtonText}>Exit VR</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  setupContainer: {
    flex: 1,
  },
  setupContent: {
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
    marginTop: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginTop: 16,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  infoCard: {
    backgroundColor: 'rgba(90, 200, 250, 0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  infoRow: {
    flexDirection: 'row',
    gap: 12,
  },
  infoContent: {
    flex: 1,
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    lineHeight: 20,
  },
  modeSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  modeOptions: {
    gap: 12,
  },
  modeCard: {
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
  },
  modeTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 12,
    marginBottom: 4,
  },
  modeDescription: {
    fontSize: 14,
  },
  statsCard: {
    backgroundColor: 'rgba(0, 122, 255, 0.1)',
    borderRadius: 12,
    padding: 20,
    marginBottom: 24,
  },
  statsTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
    textAlign: 'center',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 14,
  },
  startButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 18,
    borderRadius: 12,
    gap: 12,
    marginBottom: 16,
  },
  startButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600',
  },
  noteCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    padding: 12,
    borderRadius: 8,
    marginBottom: 20,
  },
  noteText: {
    flex: 1,
    fontSize: 12,
    lineHeight: 16,
  },
  vrViewContainer: {
    flex: 1,
  },
  vrView: {
    flex: 1,
    position: 'relative',
  },
  vrPlaceholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000000',
    padding: 20,
  },
  vrPlaceholderText: {
    fontSize: 24,
    fontWeight: '600',
    marginTop: 16,
  },
  vrPlaceholderSubtext: {
    fontSize: 14,
    marginTop: 8,
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  vrControls: {
    flexDirection: 'row',
    gap: 24,
    marginTop: 32,
  },
  vrControlHint: {
    alignItems: 'center',
    gap: 8,
  },
  vrControlText: {
    fontSize: 12,
  },
  stopButton: {
    position: 'absolute',
    bottom: 40,
    left: 20,
    right: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  stopButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default VRScreen;

