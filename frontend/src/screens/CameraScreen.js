import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Alert,
  TouchableOpacity,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import * as FileSystem from 'expo-file-system/legacy';
import Constants from 'expo-constants';
import Svg, { Circle, Line, G } from 'react-native-svg';
import { colors } from '../theme/colors';
import TopBar from '../components/TopBar';
import PrimaryButton from '../components/Button';
import LoadingOverlay from '../components/LoadingOverlay';

const getApiUrl = () => {
  // Allow explicit override from environment for reliability.
  const envUrl = process.env.EXPO_PUBLIC_API_URL;
  if (envUrl && envUrl.trim()) {
    return `${envUrl.replace(/\/$/, '')}/analyze-json`;
  }

  const extractHost = (raw) => {
    if (!raw || typeof raw !== 'string') return null;
    // Handles values like "192.168.1.10:8081" and "exp://192.168.1.10:8081".
    const noScheme = raw.includes('://') ? raw.split('://')[1] : raw;
    const hostPart = noScheme.split('/')[0];
    return hostPart.split(':')[0] || null;
  };

  // On a real device, derive the host from Expo's current dev host.
  const host =
    extractHost(Constants?.expoConfig?.hostUri) ||
    extractHost(Constants?.linkingUri) ||
    extractHost(Constants?.manifest2?.extra?.expoGo?.debuggerHost) ||
    extractHost(Constants?.manifest?.debuggerHost);

  if (host) {
    return `http://${host}:8000/analyze-json`;
  }

  // Fall back for local web/simulator workflows.
  return 'http://127.0.0.1:8000/analyze-json';
};

const API_URL = getApiUrl();
const MAX_DURATION = 15; 

const MONO_FONT = Platform.select({
  web: 'SF Mono, Monaco, Consolas, monospace',
  default: 'ui-monospace, SF Mono, JetBrains Mono, Menlo, monospace',
});

// ---------- Idle Screen ----------
function IdleScreen({ onRecord, onUpload }) {
  return (
    <View style={idleStyles.container}>
      <TopBar title="Injury Risk AI" />
      <View style={idleStyles.diagramBox}>
        <Svg viewBox="0 0 220 240" width="60%" height={160}>
          <G stroke={colors.chalkDim} strokeWidth="4" strokeLinecap="round" fill="none">
            <Circle cx="110" cy="34" r="16" />
            <Line x1="110" y1="50" x2="110" y2="140" />
            <Line x1="110" y1="70" x2="70" y2="95" />
            <Line x1="70" y1="95" x2="55" y2="140" />
            <Line x1="110" y1="70" x2="150" y2="95" />
            <Line x1="150" y1="95" x2="170" y2="120" />
            <Line x1="110" y1="140" x2="85" y2="190" />
            <Line x1="85" y1="190" x2="80" y2="228" />
            <Line x1="110" y1="140" x2="135" y2="190" />
            <Line x1="135" y1="190" x2="140" y2="228" />
          </G>
        </Svg>
        <View style={idleStyles.frameBorder} />
        <Text style={idleStyles.diagramHint}>SIDE-ON · FULL BODY · GOOD LIGHT</Text>
      </View>
      <View style={idleStyles.textBlock}>
        <Text style={idleStyles.heading}>Record your serve or stroke</Text>
        <Text style={idleStyles.subtext}>
          Stand side-on to the camera, 3–4m back, so your full body stays in frame through the swing.
        </Text>
      </View>
      <View style={idleStyles.buttonGroup}>
        <PrimaryButton icon="▶" onPress={onRecord} tone="ball">Record video</PrimaryButton>
        <PrimaryButton icon="➜]" onPress={onUpload} tone="outline">Upload from library</PrimaryButton>
      </View>
      <View style={idleStyles.disclaimer}>
        <Text style={idleStyles.disclaimerIcon}>ⓘ</Text>
        <Text style={idleStyles.disclaimerText}>
          This gives form feedback, not a medical diagnosis. Talk to a physio for pain or a suspected injury.
        </Text>
      </View>
    </View>
  );
}

const idleStyles = StyleSheet.create({
  container: { paddingHorizontal: 20, paddingBottom: 24, flex: 1, justifyContent: 'space-between', backgroundColor: colors.ink },
  diagramBox: { flex: 1, borderRadius: 20, borderWidth: 1, borderStyle: 'dashed', borderColor: colors.line, backgroundColor: colors.ink2, alignItems: 'center', justifyContent: 'center', marginBottom: 18, position: 'relative' },
  frameBorder: { position: 'absolute', top: 12, left: 12, right: 12, bottom: 12, borderWidth: 1, borderColor: colors.line, borderRadius: 14 },
  diagramHint: { position: 'absolute', bottom: 14, fontSize: 11, color: colors.chalkDim, letterSpacing: 0.5 },
  textBlock: { marginBottom: 18 },
  heading: { fontSize: 20, fontWeight: '700', color: colors.chalk, marginBottom: 6, lineHeight: 26 },
  subtext: { fontSize: 13.5, color: colors.chalkDim, lineHeight: 20 },
  buttonGroup: { gap: 10, marginBottom: 18 },
  disclaimer: { flexDirection: 'row', gap: 8, alignItems: 'flex-start' },
  disclaimerIcon: { fontSize: 14, color: colors.chalkDim, marginTop: 1 },
  disclaimerText: { flex: 1, fontSize: 11.5, color: colors.chalkDim, lineHeight: 17 },
});

// ---------- Recording Overlay ----------
function RecordingScreen({ seconds, onStop, onCancel }) {
  return (
    <View style={recStyles.container}>
      <View style={recStyles.topBar}>
        <View style={recStyles.recIndicator} />
        <Text style={recStyles.timer}>
          REC {String(Math.floor(seconds / 60)).padStart(1, '0')}:{String(seconds % 60).padStart(2, '0')}
        </Text>
        <Text style={recStyles.maxTime}>MAX 0:{String(MAX_DURATION).padStart(2, '0')}</Text>
      </View>
      <View style={recStyles.controls}>
        <TouchableOpacity onPress={onCancel} style={recStyles.cancelBtn} accessibilityLabel="Cancel recording">
          <Text style={recStyles.cancelIcon}>✕</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={onStop} style={recStyles.stopBtn} accessibilityLabel="Stop and use this take" />
        <View style={recStyles.spacer} />
      </View>
    </View>
  );
}

const recStyles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'space-between',
    padding: 20,
    paddingBottom: 28,
    zIndex: 100,
  },
  topBar: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingTop: 50 },
  recIndicator: { width: 9, height: 9, borderRadius: 4.5, backgroundColor: colors.high },
  timer: { fontFamily: MONO_FONT, fontSize: 13, letterSpacing: 1, color: colors.chalk },
  maxTime: { marginLeft: 'auto', fontFamily: MONO_FONT, fontSize: 12, color: colors.chalkDim },
  controls: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 28 },
  cancelBtn: { backgroundColor: colors.ink2, borderWidth: 1, borderColor: colors.line, width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  cancelIcon: { fontSize: 18, color: colors.chalk },
  stopBtn: { width: 68, height: 68, borderRadius: 34, backgroundColor: colors.high, borderWidth: 4, borderColor: `${colors.chalk}22` },
  spacer: { width: 44 },
});

// ---------- Main Component ----------
export default function CameraScreen({ onNavigate }) {
  const [permission, requestPermission] = useCameraPermissions();
  const [screenState, setScreenState] = useState('idle');
  const [recSeconds, setRecSeconds] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [analyzeStep, setAnalyzeStep] = useState(0);
  const [cameraReady, setCameraReady] = useState(false);
  const cameraRef = useRef(null);
  const timerRef = useRef(null);
  const recordingCancelledRef = useRef(false);

  useEffect(() => {
    (async () => {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission required', 'We need access to your media library to upload videos.');
      }
    })();
  }, []);

  useEffect(() => {
    if (screenState === 'recording') {
      setRecSeconds(0);
      timerRef.current = setInterval(() => {
        setRecSeconds((s) => (s < MAX_DURATION ? s + 1 : s));
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [screenState]);

  useEffect(() => {
    if (screenState === 'recording' && cameraReady && cameraRef.current) {
      cameraRef.current.recordAsync({ maxDuration: MAX_DURATION })
        .then((video) => {
          if (recordingCancelledRef.current) return;
          if (video && video.uri) {
            setScreenState('uploading');
            setIsLoading(true);
            sendVideo(video.uri);
          }
        })
        .catch((err) => {
          if (recordingCancelledRef.current) return;
          console.error('Recording error:', err);
          Alert.alert('Recording Error', 'Failed to record video.');
          setScreenState('idle');
          setIsLoading(false);
        });
    }
  }, [screenState, cameraReady]);

  useEffect(() => {
    if (screenState === 'analyzing') {
      const stepInterval = setInterval(() => {
        setAnalyzeStep((prev) => Math.min(prev + 1, 2));
      }, 2000);
      return () => clearInterval(stepInterval);
    } else {
      setAnalyzeStep(0);
    }
  }, [screenState]);

  const onCameraReady = useCallback(() => setCameraReady(true), []);

  const handleRecord = () => {
    recordingCancelledRef.current = false;
    setCameraReady(false);
    setScreenState('recording');
    setIsLoading(false);
  };

  const handleStopRecording = () => {
    if (cameraRef.current) cameraRef.current.stopRecording();
  };

  const handleCancelRecording = () => {
    recordingCancelledRef.current = true;
    if (cameraRef.current) cameraRef.current.stopRecording();
    setScreenState('idle');
    setIsLoading(false);
  };

  const handleUpload = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: 'videos',
        allowsEditing: true,
        quality: 1,
      });
      if (!result.canceled && result.assets[0]?.uri) {
        setScreenState('uploading');
        setIsLoading(true);
        setUploadProgress(0);
        const progressInterval = setInterval(() => {
          setUploadProgress((p) => Math.min(p + 10, 90));
        }, 200);
        await sendVideo(result.assets[0].uri);
        clearInterval(progressInterval);
        setUploadProgress(100);
      }
    } catch (error) {
      Alert.alert('Upload Error', 'Failed to pick video from library.');
      setScreenState('idle');
      setIsLoading(false);
    }
  };

  // ---------- sendVideo using Base64 JSON (avoids FormData issues) ----------
  const sendVideo = async (uri) => {
    try {
      // 1. Read the video file as a Base64 string
      const base64 = await FileSystem.readAsStringAsync(uri, {
        encoding: FileSystem.EncodingType.Base64,
      });

      // 2. Get file name from URI
      const fileName = uri.split('/').pop() || 'video.mp4';

      // 3. Create an AbortController with 180s timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 180000);

      // 4. Send as JSON
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file: base64,
          filename: fileName,
          type: 'video/mp4',
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Analysis failed');

      // 5. Navigate to results
      setScreenState('analyzing');
      setTimeout(() => {
        setIsLoading(false);
        if (onNavigate) onNavigate('Results', { result: data });
      }, 500);
    } catch (error) {
      if (error.name === 'AbortError') {
        Alert.alert('Timeout', 'The analysis took too long. Please try with a shorter video.');
      } else {
        Alert.alert(
          'Analysis Error',
          `${error.message || 'Network error.'}\n\nEndpoint: ${API_URL}`
        );
      }
      setScreenState('idle');
      setIsLoading(false);
    }
  };

  // ---------- Camera permission ----------
  if (!permission) {
    return <View style={{ flex: 1, backgroundColor: colors.ink }} />;
  }

  if (!permission.granted) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: colors.ink }}>
        <View style={styles.permissionContainer}>
          <Text style={styles.permissionIcon}>📷</Text>
          <Text style={styles.permissionTitle}>Camera Access Required</Text>
          <Text style={styles.permissionMessage}>
            We need camera access to record tennis serves and strokes for analysis.
          </Text>
          <PrimaryButton onPress={requestPermission} style={styles.permissionButton}>
            Grant Permission
          </PrimaryButton>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: colors.ink }}>
      {Platform.OS !== 'web' && (
        <CameraView
          style={StyleSheet.absoluteFill}
          ref={cameraRef}
          mode="video"
          facing="back"
          onCameraReady={onCameraReady}
        />
      )}

      {screenState !== 'recording' ? (
        <SafeAreaView style={{ flex: 1, backgroundColor: screenState === 'idle' ? colors.ink : 'transparent' }}>
          <IdleScreen onRecord={handleRecord} onUpload={handleUpload} />
        </SafeAreaView>
      ) : (
        <RecordingScreen
          seconds={recSeconds}
          onStop={handleStopRecording}
          onCancel={handleCancelRecording}
        />
      )}

      {screenState === 'uploading' && (
        <LoadingOverlay visible mode="uploading" progress={uploadProgress} />
      )}
      {screenState === 'analyzing' && (
        <LoadingOverlay visible mode="analyzing" analyzeStep={analyzeStep} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  permissionContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40, backgroundColor: colors.ink },
  permissionIcon: { fontSize: 64, marginBottom: 20 },
  permissionTitle: { fontSize: 22, fontWeight: 'bold', color: colors.chalk, marginBottom: 12 },
  permissionMessage: { fontSize: 16, color: colors.chalkDim, textAlign: 'center', lineHeight: 24, marginBottom: 28 },
  permissionButton: { minWidth: 200 },
});