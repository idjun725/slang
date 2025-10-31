// screens/LoginScreen.js
import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet } from 'react-native';
import { auth } from '../firebaseConfig';
import { signInWithEmailAndPassword } from 'firebase/auth';

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [pw, setPw] = useState('');
  const [msg, setMsg] = useState('');

  const signIn = async () => {
    try {
      await signInWithEmailAndPassword(auth, email.trim(), pw);
      setMsg('로그인 성공');
    } catch (e) {
      setMsg(e.message || '로그인 실패');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>이메일 로그인</Text>

      <TextInput
        placeholder="you@example.com"
        placeholderTextColor="#888"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
        style={styles.input}
      />
      <TextInput
        placeholder="비밀번호"
        placeholderTextColor="#888"
        value={pw}
        onChangeText={setPw}
        secureTextEntry
        style={styles.input}
      />

      <View style={styles.row}>
        <Button title="로그인" onPress={signIn} />
        <View style={{ width: 12 }} />
        <Button title="회원가입으로" onPress={() => navigation.navigate('Register')} />
      </View>

      <Text style={styles.muted}>{msg}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex:1, padding:16, backgroundColor:'#0b0b0b' },
  title: { color:'white', fontSize:22, fontWeight:'700', marginBottom:12 },
  input: {
    color:'white', borderBottomWidth:1, borderBottomColor:'#333',
    paddingVertical:8, marginBottom:12, minWidth:160
  },
  row: { flexDirection:'row', alignItems:'center', marginTop:8 },
  muted: { color:'#9aa0a6', marginTop:8 },
});
