import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';

export default function MetricItem({ label, value, unit }) {
  // Format the label: remove underscores, title case
  const formattedLabel = label
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <View style={styles.container}>
      <Text style={styles.label}>{formattedLabel}</Text>
      <View style={styles.valueRow}>
        <Text style={styles.value}>{value}</Text>
        <Text style={styles.unit}>{unit}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '48%',
    backgroundColor: colors.background,
    padding: 14,
    borderRadius: 10,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: colors.border,
  },
  label: {
    fontSize: 12,
    color: colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    fontWeight: '600',
    marginBottom: 4,
  },
  valueRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  value: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  unit: {
    fontSize: 14,
    color: colors.textSecondary,
    fontWeight: '500',
    marginLeft: 2,
  },
});

