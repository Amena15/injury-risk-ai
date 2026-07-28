import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import CameraScreen from '../screens/CameraScreen';
import ResultsScreen from '../screens/ResultsScreen';
import { colors } from '../theme/colors';

const Stack = createNativeStackNavigator();

export default function AppNavigator() {
  return (
    <Stack.Navigator
      initialRouteName="Camera"
      screenOptions={{
        headerShown: false,
        contentStyle: {
          backgroundColor: colors.ink,
        },
      }}
    >
      <Stack.Screen
        name="Camera"
        component={CameraScreen}
      />
      <Stack.Screen
        name="Results"
        component={ResultsScreen}
      />
    </Stack.Navigator>
  );
}
