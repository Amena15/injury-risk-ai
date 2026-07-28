import React, { useState } from 'react';
import { StatusBar } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import CameraScreen from './src/screens/CameraScreen';
import ResultsScreen from './src/screens/ResultsScreen';
import { colors } from './src/theme/colors';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState('Camera');
  const [resultsData, setResultsData] = useState(null);

  const navigate = (screen, params = {}) => {
    if (params.result) {
      setResultsData(params.result);
    }
    setCurrentScreen(screen);
  };

  const goBack = () => {
    setCurrentScreen('Camera');
    setResultsData(null);
  };

  return (
    <SafeAreaProvider>
      <StatusBar barStyle="light-content" backgroundColor={colors.ink} />
      {currentScreen === 'Camera' ? (
        <CameraScreen onNavigate={navigate} />
      ) : (
        <ResultsScreen result={resultsData} onBack={goBack} />
      )}
    </SafeAreaProvider>
  );
}
