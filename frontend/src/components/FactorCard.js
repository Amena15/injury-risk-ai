import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';

export default function FactorCard({ item, open, onToggle }) {
  return (
    <View style={styles.card}>
      <TouchableOpacity
        onPress={onToggle}
        accessibilityRole="button"
        accessibilityState={{ expanded: open }}
        style={styles.header}
      >
        <Text style={styles.icon}>⚠</Text>
        <Text style={styles.title} numberOfLines={1}>{item.title}</Text>
        <Text style={styles.chevron}>{open ? '▲' : '▼'}</Text>
      </TouchableOpacity>
      {open && (
        <View style={styles.body}>
          <Text style={styles.detail}>{item.detail}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 8,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    padding: 12,
    paddingHorizontal: 14,
    backgroundColor: colors.ink2,
  },
  icon: {
    fontSize: 16,
    color: colors.moderate,
  },
  title: {
    flex: 1,
    fontSize: 13.5,
    fontWeight: '600',
    color: colors.chalk,
  },
  chevron: {
    fontSize: 12,
    color: colors.chalkDim,
  },
  body: {
    paddingHorizontal: 14,
    paddingBottom: 14,
  },
  detail: {
    fontSize: 12.5,
    color: colors.chalkDim,
    lineHeight: 19,
  },
});

