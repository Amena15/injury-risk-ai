import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';

export default function PrimaryButton({ children, onPress, icon, tone = 'ball', disabled, style }) {
  const isBall = tone === 'ball';
  const bgColor = disabled ? colors.line : isBall ? colors.ball : 'transparent';
  const textColor = disabled ? colors.chalkDim : isBall ? colors.ink : colors.chalk;
  const border = disabled
    ? 'none'
    : isBall
    ? 'none'
    : { borderWidth: 1, borderColor: colors.line };

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled}
      activeOpacity={0.8}
      style={[
        styles.button,
        { backgroundColor: bgColor },
        border,
        style,
      ]}
    >
      {icon && <Text style={[styles.icon, { color: textColor }]}>{icon}</Text>}
      <Text style={[styles.text, { color: textColor }]}>{children}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    width: '100%',
    borderRadius: 14,
    paddingVertical: 15,
    paddingHorizontal: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  text: {
    fontSize: 15,
    fontWeight: '700',
    fontFamily: '-apple-system, Segoe UI, Inter, sans-serif',
  },
  icon: {
    fontSize: 18,
  },
});

