import React from 'react';
import { View, StyleSheet } from 'react-native';
import Svg, { Circle, Line, G, Text as SvgText } from 'react-native-svg';
import { colors } from '../theme/colors';

// Joint positions for the stick figure
const JOINT_POS = {
  right_elbow: [138, 118],
  left_elbow: [70, 95],
  right_shoulder: [150, 70],
  left_shoulder: [70, 70],
  right_knee: [135, 190],
  left_knee: [85, 190],
  hip: [110, 140],
};

export default function BodyDiagram({ flag }) {
  const [fx, fy] = JOINT_POS[flag] || [138, 118];
  const isFlagged = flag && flag !== 'none';

  return (
    <View style={styles.container}>
      <Svg viewBox="0 0 220 240" width="100%" height={200}>
        <G stroke={colors.chalkDim} strokeWidth="4" strokeLinecap="round" fill="none">
          {/* Head */}
          <Circle cx="110" cy="34" r="16" fill="none" />
          {/* Spine */}
          <Line x1="110" y1="50" x2="110" y2="140" />
          {/* Left arm */}
          <Line x1="110" y1="70" x2="70" y2="95" />
          <Line x1="70" y1="95" x2="55" y2="140" />
          {/* Right arm */}
          <Line x1="110" y1="70" x2="150" y2="95" />
          <Line x1="150" y1="95" x2="138" y2="118" />
          <Line x1="138" y1="118" x2="168" y2="130" />
          {/* Left leg */}
          <Line x1="110" y1="140" x2="85" y2="190" />
          <Line x1="85" y1="190" x2="80" y2="228" />
          {/* Right leg */}
          <Line x1="110" y1="140" x2="135" y2="190" />
          <Line x1="135" y1="190" x2="140" y2="228" />
        </G>

        {isFlagged && (
          <>
            {/* Animated pulse ring */}
            <Circle
              cx={fx}
              cy={fy}
              r="9"
              fill="none"
              stroke={colors.high}
              strokeWidth="2.5"
            />
            {/* Center dot */}
            <Circle cx={fx} cy={fy} r="4" fill={colors.high} />
            {/* Callout line */}
            <Line
              x1={fx}
              y1={fy}
              x2={fx + 45}
              y2={fy - 40}
              stroke={colors.high}
              strokeWidth="1.5"
              strokeDasharray="3,3"
            />
            {/* Angle label */}
            <SvgText
              x={fx + 48}
              y={fy - 42}
              fill={colors.high}
              fontSize="12"
              fontWeight="700"
            >
              128°
            </SvgText>
          </>
        )}
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.ink2,
    padding: 10,
    paddingBottom: 4,
    marginBottom: 18,
    alignItems: 'center',
  },
});

