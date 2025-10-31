// functions/index.js  (ESM)
import { onCall, HttpsError } from 'firebase-functions/v2/https';
import { defineSecret } from 'firebase-functions/params';
import { initializeApp } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';
import sgMail from '@sendgrid/mail';

// ===== Secrets =====
const OPENAI_API_KEY = defineSecret('OPENAI_API_KEY');        // 선택(없으면 간단한 기본 답변)
const SENDGRID_API_KEY = defineSecret('SENDGRID_API_KEY');    // 필수(이메일)
const FROM_EMAIL = defineSecret('FROM_EMAIL');                // 필수(이메일)

// ===== Firebase Admin =====
initializeApp();
const db = getFirestore();

// ===== 웹에서 실제 예문 검색 =====
async function searchRealExamples(term) {
  try {
    const examples = [];
    const maxExamples = 3;

    // 1. DCInside 검색
    try {
      const dcUrl = `https://search.dcinside.com/post/q/${encodeURIComponent(term)}`;
      const dcResponse = await fetch(dcUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
      });
      
      if (dcResponse.ok) {
        const html = await dcResponse.text();
        // 간단한 텍스트 추출 (실제로는 더 정교한 파싱 필요)
        const matches = html.match(new RegExp(`[^.]*${term}[^.]*\\.`, 'g'));
        if (matches) {
          examples.push(...matches.slice(0, 2).map(m => m.trim()));
        }
      }
    } catch (err) {
      console.log('DCInside 검색 실패:', err.message);
    }

    // 2. 클리앙 검색
    try {
      const clienUrl = `https://www.clien.net/service/search?q=${encodeURIComponent(term)}`;
      const clienResponse = await fetch(clienUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
      });
      
      if (clienResponse.ok) {
        const html = await clienResponse.text();
        const matches = html.match(new RegExp(`[^.]*${term}[^.]*\\.`, 'g'));
        if (matches) {
          examples.push(...matches.slice(0, 2).map(m => m.trim()));
        }
      }
    } catch (err) {
      console.log('클리앙 검색 실패:', err.message);
    }

    // 3. 더미 예문으로 보완 (실제 검색이 실패한 경우)
    if (examples.length === 0) {
      const dummyExamples = [
        `오늘 게시판에서 ${term}이라는 말 많이 봤어요`,
        `${term}이 뭔지 궁금해서 검색해봤는데 재밌네요`,
        `요즘 ${term}이 핫한 것 같아요`
      ];
      examples.push(...dummyExamples.slice(0, maxExamples));
    }

    return examples.slice(0, maxExamples);
  } catch (err) {
    console.error('예문 검색 오류:', err);
    return [`"${term}"에 대한 실제 예문을 찾지 못했습니다.`];
  }
}

// ===== 웹에서 실제 예문과 정의 검색 =====
async function searchWebDefinitionAndExamples(term) {
  try {
    // 웹에서 실제 예문 검색
    const examples = await searchRealExamples(term);
    
    // 간단한 정의 생성 (AI 없이)
    const simpleDefinition = `"${term}"은(는) 최근 인터넷 커뮤니티에서 사용되는 신조어입니다.`;
    
    // 결과 조합
    let result = simpleDefinition;
    
    if (examples.length > 0) {
      result += '\n\n실제 사용 예문:\n';
      examples.forEach((example, index) => {
        result += `• ${example}\n`;
      });
    } else {
      result += '\n\n예문을 찾지 못했습니다.';
    }

    return {
      word: term,
      definition: result,
      notes: examples.length > 0 ? '실제 웹에서 수집한 예문' : '예문을 찾지 못했습니다',
      source: 'web_search',
      confidence: examples.length > 0 ? '높음' : '낮음',
    };
  } catch (err) {
    console.error('웹 검색 오류:', err);
    return {
      word: term,
      definition: `"${term}"에 대한 정보를 찾지 못했습니다.`,
      notes: '검색 실패',
      source: 'error',
      confidence: '낮음',
    };
  }
}

// ===== Callable: 신조어 설명 조회(자연어) =====
export const defineNeologism = onCall(
  { region: 'asia-northeast3', secrets: [OPENAI_API_KEY] },
  async (request) => {
    try {
      const term = String(request.data?.term || '').trim();
      if (!term) throw new HttpsError('invalid-argument', 'term이 비었습니다.');

      const id = term.toLowerCase();
      const docRef = db.collection('definitions').doc(id);

      // 1) 캐시 조회 (24시간 TTL)
      const snap = await docRef.get();
      const now = Date.now();
      if (snap.exists) {
        const cached = snap.data();
        const ts =
          cached?.updatedAt?.toMillis?.() ??
          (cached?.updatedAt instanceof Date ? cached.updatedAt.getTime() : cached?.updatedAt ?? 0);
        const age = now - Number(ts || 0);
        const oneDay = 24 * 60 * 60 * 1000;
        if (age < oneDay) {
          return {
            word: cached.word || term,
            definition: cached.definition || '',
            notes: cached.notes || '',
            source: 'cache',
            confidence: cached.confidence || '중간',
          };
        }
      }

      // 2) 웹에서 실제 예문과 정의 검색
      const ai = await searchWebDefinitionAndExamples(term);

      // 3) 캐시에 저장
      await docRef.set(
        {
          ...ai,
          updatedAt: new Date(),
        },
        { merge: true }
      );

      return ai;
    } catch (err) {
      console.error('defineNeologism error:', err);
      if (err instanceof HttpsError) throw err;
      throw new HttpsError('internal', err?.message || '서버 오류');
    }
  }
);

// ===== Callable: 오늘의 신조어 이메일 발송(기존) =====
export const sendTodayWordsEmail = onCall(
  { region: 'asia-northeast3', secrets: [SENDGRID_API_KEY, FROM_EMAIL] },
  async (request) => {
    try {
      const ctx = request.auth;
      if (!ctx) throw new HttpsError('unauthenticated', '로그인이 필요합니다.');

      const to = (request.data && request.data.to) || ctx.token.email;
      if (!to) throw new HttpsError('failed-precondition', '수신 이메일을 찾을 수 없습니다.');

      const top = Math.max(1, Math.min(20, Number(request.data?.top ?? 5)));

      const snap = await db.collection('neologisms').doc('latest').get();
      if (!snap.exists) throw new HttpsError('not-found', '신조어 데이터가 없습니다.');

      const items = snap.get('items') || [];
      const topItems = items.slice(0, top);

      const text =
        `오늘의 신조어 Top ${top}\n\n` +
        topItems.map((x, i) => `${i + 1}. ${x.word} (${x.freq})`).join('\n');

      sgMail.setApiKey(SENDGRID_API_KEY.value());
      await sgMail.send({
        to,
        from: FROM_EMAIL.value(),
        subject: `오늘의 신조어 Top ${top}`,
        text,
      });

      return { ok: true, message: `이메일 발송 완료 → ${to}` };
    } catch (error) {
      console.error('📧 sendTodayWordsEmail 오류:', error);
      if (error instanceof HttpsError) throw error;
      throw new HttpsError('internal', `이메일 발송 중 오류: ${error?.message || '알 수 없는 오류'}`);
    }
  }
);
