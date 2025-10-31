// screens/RegisterScreen.js
import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet } from 'react-native';
import { auth } from '../firebaseConfig';
import { createUserWithEmailAndPassword } from 'firebase/auth';

export default function RegisterScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [pw, setPw] = useState('');
  const [msg, setMsg] = useState('');

  const signUp = async () => {
    try {
      await createUserWithEmailAndPassword(auth, email.trim(), pw);
      setMsg('회원가입 & 자동 로그인 완료');
    } catch (e) {
      setMsg(e.message || '회원가입 실패');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>회원가입</Text>

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
        placeholder="비밀번호(6자 이상)"
        placeholderTextColor="#888"
        value={pw}
        onChangeText={setPw}
        secureTextEntry
        style={styles.input}
      />

      <View style={styles.row}>
        <Button title="회원가입" onPress={signUp} />
        <View style={{ width: 12 }} />
        <Button title="로그인으로" onPress={() => navigation.navigate('Login')} />
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
