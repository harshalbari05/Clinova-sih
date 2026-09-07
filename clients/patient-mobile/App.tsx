import React from 'react';
import { StyleSheet, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { AuthProvider } from './src/context/AuthContext';
import { ConsultationProvider } from './src/context/ConsultationContext';
import { RootNavigator } from './src/navigation/RootNavigator';

export default function App() {
  return (
    <View style={styles.container}>
      <StatusBar style="dark" />
      <AuthProvider>
        <ConsultationProvider>
          <RootNavigator />
        </ConsultationProvider>
      </AuthProvider>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#faf8ff',
  },
});
