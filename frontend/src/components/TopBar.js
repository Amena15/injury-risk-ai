import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';

export default function TopBar({ title, onBack }) {
  return (
    <View style={styles.container}>
      {onBack ? (
        <TouchableOpacity onPress={onBack} style={styles.backButton} aria-label="Go back">
          <Text style={styles.backIcon}>←</Text>
        </TouchableOpacity>
      ) : (
        <View style={styles.placeholder} />
      )}
      <Text style={styles.title}>{title}</Text>
      <View style={styles.placeholder} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 6,
    paddingBottom: 18,
  },
  backButton: {
    padding: 4,
  },
  backIcon: {
    color: colors.chalkDim,
    fontSize: 22,
  },
  title: {
    fontSize: 13,
    letterSpacing: 1.5,
    textTransform: 'uppercase',
    color: colors.chalkDim,
    fontWeight: '600',
  },
  placeholder: {
    width: 30,
  },
});

