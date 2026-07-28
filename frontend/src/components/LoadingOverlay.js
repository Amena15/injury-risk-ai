import React, { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, Animated, Easing } from 'react-native';
import { colors } from '../theme/colors';

const ANALYZE_STEPS = [
  'Detecting pose',
  'Calculating joint angles',
  'Assessing risk factors',
];

export default function LoadingOverlay({ visible, mode = 'analyzing', progress = 0, analyzeStep = 0 }) {
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;
  const [progressWidth, setProgressWidth] = useState(0);

  useEffect(() => {
    if (visible) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 0.6,
            duration: 800,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 800,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
        ])
      ).start();

      Animated.loop(
        Animated.timing(rotateAnim, {
          toValue: 1,
          duration: 1500,
          easing: Easing.linear,
          useNativeDriver: true,
        })
      ).start();

      if (mode === 'uploading') {
        const interval = setInterval(() => {
          setProgressWidth((prev) => Math.min(prev + 5, 98));
        }, 200);
        return () => clearInterval(interval);
      }
    } else {
      pulseAnim.setValue(1);
      rotateAnim.setValue(0);
      setProgressWidth(0);
    }
  }, [visible, mode]);

  if (!visible) return null;

  const rotate = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const displayProgress = mode === 'uploading' ? Math.max(progress, progressWidth) : 0;

  return (
    <View style={styles.overlay}>
      <View style={styles.card}>
        {mode === 'uploading' ? (
          // Uploading mode: progress bar
          <>
            <Text style={styles.uploadIcon}>↑</Text>
            <Text style={styles.message}>Uploading clip</Text>
            <View style={styles.progressBar}>
              <View
                style={[
                  styles.progressFill,
                  { width: `${Math.min(displayProgress, 100)}%` },
                ]}
              />
            </View>
            <Text style={styles.progressText}>{Math.min(displayProgress, 100)}%</Text>
          </>
        ) : (
          // Analyzing mode: step checklist
          <>
            <Animated.View
              style={[
                styles.spinner,
                {
                  opacity: pulseAnim,
                  transform: [{ rotate }],
                },
              ]}
            >
              <View style={styles.spinnerInner} />
            </Animated.View>
            <View style={styles.stepsContainer}>
              {ANALYZE_STEPS.map((step, i) => (
                <View key={step} style={[styles.stepRow, { opacity: i <= analyzeStep ? 1 : 0.35 }]}>
                  <Text style={styles.stepIcon}>
                    {i < analyzeStep ? '✓' : i === analyzeStep ? '○' : '○'}
                  </Text>
                  <Text style={[
                    styles.stepText,
                    i < analyzeStep && styles.stepDone,
                    i === analyzeStep && styles.stepActive,
                  ]}>
                    {step}{i === analyzeStep ? '…' : ''}
                  </Text>
                </View>
              ))}
            </View>
          </>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  card: {
    backgroundColor: colors.panel,
    borderRadius: 20,
    padding: 36,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.15,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 8 },
    elevation: 10,
    minWidth: 240,
    borderWidth: 1,
    borderColor: colors.line,
  },
  // Uploading mode
  uploadIcon: {
    fontSize: 28,
    color: colors.ball,
    marginBottom: 14,
  },
  progressBar: {
    width: '100%',
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.line,
    overflow: 'hidden',
    marginTop: 12,
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.ball,
    borderRadius: 3,
  },
  progressText: {
    fontFamily: 'ui-monospace, SF Mono, JetBrains Mono, Menlo, monospace',
    fontSize: 13,
    color: colors.chalkDim,
    marginTop: 8,
  },
  // Analyzing mode
  spinner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    borderWidth: 4,
    borderColor: colors.line,
    borderTopColor: colors.ball,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  spinnerInner: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: colors.ball,
  },
  message: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.chalk,
    marginBottom: 4,
  },
  stepsContainer: {
    width: '100%',
    gap: 14,
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  stepIcon: {
    fontSize: 18,
    color: colors.ball,
    width: 22,
  },
  stepText: {
    fontSize: 14,
    color: colors.chalk,
  },
  stepDone: {
    color: colors.low,
  },
  stepActive: {
    color: colors.ball,
  },
});

