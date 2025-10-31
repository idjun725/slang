// screens/HomeScreen.js
import React, { useEffect, useState, useCallback } from 'react';
import {
  SafeAreaView, View, Text, FlatList, ActivityIndicator,
  TextInput, RefreshControl, StyleSheet, Button, ScrollView
} from 'react-native';

import { auth, db, functions } from '../firebaseConfig';
import { doc, onSnapshot, getDoc } from 'firebase/firestore';
import { httpsCallable } from 'firebase/functions';
import { signOut } from 'firebase/auth';

export default function HomeScreen() {
  // 랭킹 데이터
  const [items, setItems] = useState([]);
  const [updatedAt, setUpdatedAt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [msg, setMsg] = useState('');

  // 신조어 검색
  const [query, setQuery] = useState('');
  const [lookupBusy, setLookupBusy] = useState(false);
  const [lookupErr, setLookupErr] = useState('');
  const [lookupRes, setLookupRes] = useState(null);

  // Firestore 실시간 구독
  useEffect(() => {
    const unsub = onSnapshot(
      doc(db, 'neologisms', 'latest'),
      (snap) => {
        if (!snap.exists()) {
          setItems([]);
          setUpdatedAt(null);
          setLoading(false);
          setError('데이터가 없습니다.');
          return;
        }
        const data = snap.data() || {};
        const list = (data.items || []).sort((a, b) => (b.freq || 0) - (a.freq || 0));
        setItems(list);
        const ts = data.updatedAt?.toDate?.() ?? (data.date ? new Date(data.date) : null);
        setUpdatedAt(ts);
        setError('');
        setLoading(false);
      },
      (err) => {
        setError(err?.message || '실시간 구독 오류');
        setLoading(false);
      }
    );
    return () => unsub();
  }, []);

  // 랭킹 새로고침
  const onRefresh = useCallback(async () => {
    try {
      setRefreshing(true);
      const snap = await getDoc(doc(db, 'neologisms', 'latest'));
      if (snap.exists()) {
        const data = snap.data() || {};
        const list = (data.items || []).sort((a, b) => (b.freq || 0) - (a.freq || 0));
        setItems(list);
        setUpdatedAt(data.updatedAt?.toDate?.() ?? null);
      }
    } catch (e) {
      setError(e?.message || '새로고침 실패');
    } finally {
      setRefreshing(false);
    }
  }, []);

  // 오늘의 신조어 이메일 발송
  const sendEmail = async () => {
    try {
      if (!auth.currentUser?.email) {
        setMsg('이메일로 로그인 후 이용하세요.');
        return;
      }
      const fn = httpsCallable(functions, 'sendTodayWordsEmail');
      const res = await fn({ top: 5 });
      setMsg(res.data?.message || '이메일 발송 요청 완료');
    } catch (e) {
      setMsg(`발송 실패: ${e?.message || ''}`);
    }
  };

  // 로그아웃
  const handleSignOut = async () => {
    await signOut(auth);
  };


  // 신조어 정의 조회
  const runLookup = useCallback(async () => {
    const term = query.trim();
    if (!term) return;
    setLookupErr('');
    setLookupRes(null);
    setLookupBusy(true);
    try {
      const fn = httpsCallable(functions, 'defineNeologism');
      const { data } = await fn({ term });
      setLookupRes(data);
    } catch (e) {
      setLookupErr(e?.message || '조회 실패');
    } finally {
      setLookupBusy(false);
    }
  }, [query]);

  if (loading) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator />
        <Text style={styles.muted}>불러오는 중…</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* 상단 */}
      <View style={styles.header}>
        <Text style={styles.title}>신조어 랭킹</Text>
        {updatedAt && <Text style={styles.muted}>업데이트: {updatedAt.toLocaleString()}</Text>}
        <Text style={styles.muted}>로그인: {auth.currentUser?.email}</Text>
        <View style={styles.buttonRow}>
          <Button title="이메일 보내기" onPress={sendEmail} />
          <Button title="로그아웃" onPress={handleSignOut} />
        </View>
        <Text style={styles.muted}>{msg}</Text>
      </View>

      {/* 신조어 검색 */}
      <View style={styles.searchBox}>
        <Text style={styles.subTitle}>신조어 검색 (설명/예문)</Text>
        <View style={styles.searchRow}>
          <TextInput
            placeholder="예: ㄹㅇㅋㅋ, 느좋남"
            value={query}
            onChangeText={setQuery}
            style={styles.search}
            autoCorrect={false}
            clearButtonMode="while-editing"
            placeholderTextColor="#888"
            onSubmitEditing={runLookup}
          />
          <Button title="검색" onPress={runLookup} />
        </View>

        {lookupBusy && <ActivityIndicator style={{ marginTop: 12 }} />}
        {lookupErr ? <Text style={styles.error}>⚠️ {lookupErr}</Text> : null}

        {lookupRes && (
          <ScrollView style={styles.card}>
            <Text style={styles.word}>{lookupRes.word}</Text>
            <Text style={styles.def}>{lookupRes.definition}</Text>
            {lookupRes.notes && <Text style={styles.notes}>참고: {lookupRes.notes}</Text>}

            {lookupRes.examples?.length > 0 && (
              <>
                <Text style={styles.sub}>예문</Text>
                {lookupRes.examples.map((ex, i) => (
                  <Text key={i} style={styles.li}>• {ex}</Text>
                ))}
              </>
            )}

            {lookupRes.synonyms?.length > 0 && (
              <>
                <Text style={styles.sub}>유사어</Text>
                <Text style={styles.li}>{lookupRes.synonyms.join(', ')}</Text>
              </>
            )}

            <Text style={styles.meta}>
              출처: {lookupRes.source === 'cache' ? '캐시' : lookupRes.source === 'web_search' ? '웹 검색' : 'AI 생성'}
            </Text>
          </ScrollView>
        )}
      </View>

      {/* 랭킹 리스트 */}
      {error ? <Text style={styles.error}>⚠️ {error}</Text> : null}
      <FlatList
        data={items}
        keyExtractor={(item, idx) => `${item.word}-${idx}`}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        renderItem={({ item, index }) => (
          <View style={styles.row}>
            <Text style={styles.rank}>{index + 1}.</Text>
            <View style={{ flex: 1 }}>
              <Text style={styles.word}>{item.word}</Text>
              <Text style={styles.freq}>freq: {item.freq ?? 0}</Text>
            </View>
          </View>
        )}
        contentContainerStyle={{ paddingBottom: 24 }}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0b0b0b' },
  header: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 6 },
  title: { fontSize: 20, fontWeight: '700', color: 'white' },
  subTitle: { color: 'white', fontSize: 16, fontWeight: '700' },
  muted: { color: '#9aa0a6', marginTop: 6 },
  buttonRow: { flexDirection: 'row', gap: 12, marginTop: 8 },
  searchBox: { paddingHorizontal: 16, marginTop: 12 },
  searchRow: { flexDirection: 'row', gap: 8, alignItems: 'center', marginTop: 6 },
  search: {
    flex: 1,
    paddingHorizontal: 12, paddingVertical: 10,
    borderRadius: 12, backgroundColor: '#161616', color: 'white',
    borderWidth: 1, borderColor: '#262626',
  },
  card: { marginTop: 12, marginBottom: 8, backgroundColor: '#141414', padding: 12, borderRadius: 12 },
  def: { color: 'white', marginTop: 6 },
  notes: { color: '#9aa0a6', marginTop: 6 },
  sub: { color: 'white', fontWeight: '700', marginTop: 10 },
  li: { color: 'white', marginTop: 4 },
  meta: { color: '#9aa0a6', marginTop: 10, fontSize: 12 },
  row: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 16, paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#222',
  },
  rank: { width: 36, color: '#9aa0a6', fontWeight: '600' },
  word: { color: 'white', fontSize: 16, fontWeight: '600' },
  freq: { color: '#9aa0a6', marginTop: 2, fontSize: 12 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  error: { color: '#ff6b6b', marginHorizontal: 16, marginVertical: 8 },
});
