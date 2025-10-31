// App.js
import React, { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { auth } from './firebaseConfig';
import { onAuthStateChanged } from 'firebase/auth';

import HomeScreen from './screens/HomeScreen';
import LoginScreen from './screens/LoginScreen';
import RegisterScreen from './screens/RegisterScreen';

const Stack = createNativeStackNavigator();

export default function App() {
  const [checking, setChecking] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (u) => {
      setUser(u || null);
      setChecking(false);
    });
    return () => unsub();
  }, []);

  if (checking) {
    return (
      <View style={{ flex: 1, alignItems:'center', justifyContent:'center', backgroundColor:'#0b0b0b' }}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <NavigationContainer>
      {user ? (
        <Stack.Navigator
          screenOptions={{
            headerStyle:{ backgroundColor:'#0b0b0b' },
            headerTintColor:'white',
            contentStyle:{ backgroundColor:'#0b0b0b' }
          }}
        >
          <Stack.Screen name="Home" component={HomeScreen} options={{ title: '신조어 랭킹' }} />
        </Stack.Navigator>
      ) : (
        <Stack.Navigator
          screenOptions={{
            headerStyle:{ backgroundColor:'#0b0b0b' },
            headerTintColor:'white',
            contentStyle:{ backgroundColor:'#0b0b0b' }
          }}
        >
          <Stack.Screen name="Login" component={LoginScreen} options={{ title: '로그인' }} />
          <Stack.Screen name="Register" component={RegisterScreen} options={{ title: '회원가입' }} />
        </Stack.Navigator>
      )}
    </NavigationContainer>
  );
}
