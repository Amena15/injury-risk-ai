import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';

const getRiskColor = (level) => {
  switch (level) {
    case 'High':
      return colors.accent;
    case 'Moderate':
      return colors.warning;
    case 'Low':
    default:
      return colors.secondary;
  }
};

const getRiskEmoji = (level) => {
  switch (level) {
    case 'High':
      return '🔴';
    case 'Moderate':
      return '🟡';
    case 'Low':
    default:
      return '🟢';
  }
};

export default function RiskCard({ level, score }) {
  const color = getRiskColor(level);
  const emoji = getRiskEmoji(level);

  return (
    <View style={[styles.card, { borderLeftColor: color }]}>
      <View style={styles.header}>
        <Text style={styles.emoji}>{emoji}</Text>
        <View style={styles.headerText}>
          <Text style={styles.levelLabel}>Overall Risk Level</Text>
          <Text style={[styles.levelValue, { color }]}>{level}</Text>
        </View>
      </View>
      <View style={styles.divider} />
      <View style={styles.scoreRow}>
        <Text style={styles.scoreLabel}>Risk Score</Text>
        <Text style={styles.scoreValue}>
          {score}
          <Text style={styles.scoreUnit}> / 100</Text>
        </Text>
      </View>
      {/* Mini progress bar */}
      <View style={styles.progressBar}>
        <View
          style={[
            styles.progressFill,
            {
              width: `${Math.min(score, 100)}%`,
              backgroundColor: color,
            },
          ]}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderLeftWidth: 6,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 4,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  emoji: {
    fontSize: 32,
    marginRight: 14,
  },
  headerText: {
    flex: 1,
  },
  levelLabel: {
    fontSize: 14,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  levelValue: {
    fontSize: 28,
    fontWeight: 'bold',
    marginTop: 2,
  },
  divider: {
    height: 1,
    backgroundColor: colors.border,
    marginVertical: 12,
  },
  scoreRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  scoreLabel: {
    fontSize: 14,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  scoreValue: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  scoreUnit: {
    fontSize: 14,
    fontWeight: '400',
    color: colors.textSecondary,
  },
  progressBar: {
    height: 6,
    backgroundColor: colors.border,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
});

