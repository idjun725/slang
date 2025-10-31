# -*- coding: utf-8 -*-
import os, re, time, json, requests, math, threading, feedparser
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from konlpy.tag import Okt
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone

# =========================
# 환경설정
# =========================
MOBILE_UA = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) "
             "AppleWebKit/537.36 (KHTML, like Gecko) "
             "Chrome/124.0.0.0 Mobile Safari/537.36")
DESKTOP_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/124.0.0.0 Safari/537.36")

def _set_cdp_headers(driver, headers: dict | None):
    try:
        driver.execute_cdp_cmd("Network.enable", {})
        if headers:
            driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})
    except Exception:
        pass

def _set_cdp_ua(driver, ua: str | None):
    try:
        if ua:
            driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": ua})
    except Exception:
        pass

load_dotenv()

# (선택) OpenAI LLM 사용 여부
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
USE_LLM_FILTER = bool(OPENAI_API_KEY)

# =========================
# Selenium 수집 대상
# =========================
SOURCES = [
    {"name":"DCInside-열품타",
     "url":"https://gall.dcinside.com/board/lists?id=hot",
     "selector":"td.gall_tit > a", "wait":6, "limit":80, "ua":"desktop"},

    {"name":"DCInside-인기글",
     "url":"https://gall.dcinside.com/board/lists/?id=dcbest",
     "selector":"td.gall_tit > a", "wait":6, "limit":80, "ua":"desktop"},

    {"name":"클리앙-모두의공원",
     "url":"https://www.clien.net/service/board/park",
     "selector":"div.list_item.symph_row a.list_subject",
     "wait":6, "limit":80, "ua":"desktop"},

    # 네이트판: 모바일 + Referer
    {"name":"네이트판-일간랭킹",
     "url":"https://m.pann.nate.com/talk/ranking/d",
     "selector":"a.tit, a.subject, ul#talkRankingList li a, .list a",
     "wait":8, "limit":80, "ua":"mobile",
     "headers":{"Referer":"https://m.pann.nate.com/"}},

    # 웃긴대학: cp949 폴백
    {"name":"웃긴대학-베스트",
     "url":"http://www.humoruniv.com/board/list.html?table=pick",
     "selector":"td.li_sbj > a, a.li_sbj, .li_sbj a, table.board_list a",
     "wait":8, "limit":80, "ua":"desktop", "encoding_fallback":"cp949"},

    # 뽐뿌: 모바일 + verify=False 폴백
    {"name":"뽐뿌-유머",
     "url":"https://m.ppomppu.co.kr/new/bbs_list.php?id=humor",
     "selector":".list_title a, td.notice a, .title a",
     "wait":8, "limit":80, "ua":"mobile",
     "headers":{"Referer":"https://m.ppomppu.co.kr/"},
     "encoding_fallback":"cp949", "insecure_ok":True},
]

# =========================
# RSS
# =========================
USE_RSS = True
RSS_FEEDS = [
    "https://hnrss.org/newest",
    "https://medium.com/feed/tag/slang",
    "https://bbs.ruliweb.com/best/humor/rss",
    "https://www.instiz.net/rss/list.php?id=pt",
    "https://theqoo.net/hot/rss",
    "https://www.bobaedream.co.kr/rss/best",
    "https://section.blog.naver.com/rss/BestPost.naver",
]

HDRS = {"User-Agent": "Mozilla/5.0"}
NAVER_URL = "https://ko.dict.naver.com/api3/koko/search?query={q}&range=word&page=1"

# 2단계 선택 파라미터
TOP_STRICT_N = 30
TAIL_POOL_N  = 300
TARGET_N     = 40   # 최종 후보 목표 개수

# 소스별 가중치
SOURCE_WEIGHT = {
    "DCInside-열품타": 1.25,
    "DCInside-인기글": 1.20,
    "클리앙-모두의공원": 1.05,
    "네이트판-일간랭킹": 1.30,
    "웃긴대학-베스트": 1.25,
    "뽐뿌-유머": 1.15,
    "오늘의유머-베오베": 1.15,
    "RSS": 1.00,
}

# =========================
# 정규식/필터
# =========================
HANGUL_RE   = re.compile(r"[가-힣]")
ONLY_PUNCT  = re.compile(r"^[\W_]+$")
KLOL_RE     = re.compile(r"^[ㅋㅎㅠㅜ]+$")
EMOJI_RE    = re.compile(r"[\U00010000-\U0010FFFF]")
CHOSEONG_RE = re.compile(r"^[ㄱ-ㅎㅏ-ㅣ]{2,6}$")
MIX_KO_EN   = re.compile(r"(?=.*[A-Za-z])(?=.*[가-힣])")
REP_CHAR    = re.compile(r"(.)\1{3,}")     # 같은 문자 4회↑
NUM_KO      = re.compile(r"\d+[가-힣]|[가-힣]+\d+")

STOP = {
    # 일상 상시어
    "이건","저건","그거","오늘","어제","이번","우리","너","나","끝","진짜","생각",
    "영상","사진","공지","추천","정보","뉴스","제목","링크","댓글","작성","조회","시간","노래",
    "...","..",".","?","!","ㅋ","ㅠ","ㅇ","아","개","애옹","속보","일본","건강","건설","그동안",
    "얼마나","내","조회추천","조회","사람","아침","세계"

    # 정치·경제·뉴스 상시어
    "정부","대통령","국회","장관","의원","정당","총리","검찰","경찰","재판","국무회의","계엄",
    "윤석열","이재명","권성동","김문수","조국","김건희","구속","구속영장","구속영장발부","김건희구속","김건희구속영장","김건희구속영장발부",
    "가격","경제","주식","금리","환율","물가","부동산","기업","재정","금융","세금","기사","논란",
    "공연","감독","간부","결정","결의","경영","경멸","대폭","교도통신","한국"
}

# =========================
# 유틸
# =========================
def clean_text(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

def normalize_title(t):
    t = clean_text(t)
    t = EMOJI_RE.sub("", t)
    return clean_text(t)

def is_noisy_title(t):
    if not t: return True
    if ONLY_PUNCT.match(t): return True
    if KLOL_RE.match(t): return True
    if REP_CHAR.search(t): return True
    return False

def dedupe_keep_order(items):
    seen = set(); out = []
    for x in items:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

# =========================
# Selenium 수집
# =========================
def fetch_titles_by_selenium(driver, url, selector, wait=6, limit=80, source_name="", ua=None, headers=None):
    # UA/헤더 적용
    _set_cdp_headers(driver, headers)
    _set_cdp_ua(driver, MOBILE_UA if ua == "mobile" else DESKTOP_UA)

    driver.get(url)
    WebDriverWait(driver, wait).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    sel_list = [s.strip() for s in selector.split(",") if s.strip()]
    els, last_exc = [], None
    for sel in sel_list:
        try:
            WebDriverWait(driver, wait).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, sel))
            )
            WebDriverWait(driver, 2).until(
                EC.visibility_of_any_elements_located((By.CSS_SELECTOR, sel))
            )
            soup = BeautifulSoup(driver.page_source, "lxml")
            found = soup.select(sel)
            if found:
                els = found
                break
        except Exception as e:
            last_exc = e
            continue

    titles = []
    for el in els[:limit]:
        txt = clean_text(el.get_text(" "))
        if txt:
            titles.append(txt)

    if not titles:
        dump_path = f"debug_{(source_name or 'page').replace('/','_')}.html"
        with open(dump_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"[WARNING] {source_name or url} 0건 → HTML 덤프 저장: {dump_path}")
        if last_exc:
            print(f"   마지막 예외: {last_exc}")
    return titles

# requests 폴백 (도메인별 인코딩)
def fetch_titles_by_requests(url, selectors, timeout=8, encoding=None, limit=80, headers=None, insecure_ok=False):
    hdrs = {
        "User-Agent": MOBILE_UA if ("m." in url) else DESKTOP_UA,
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": url,
    }
    if headers:
        hdrs.update(headers)

    try:
        r = requests.get(url, headers=hdrs, timeout=timeout, verify=not insecure_ok)
    except requests.exceptions.SSLError:
        if insecure_ok:
            r = requests.get(url, headers=hdrs, timeout=timeout, verify=False)
        else:
            return []
    if encoding:
        r.encoding = encoding
    soup = BeautifulSoup(r.text, "lxml")
    for sel in [s.strip() for s in selectors.split(",") if s.strip()]:
        els = soup.select(sel)
        if els:
            out = []
            for el in els[:limit]:
                txt = clean_text(el.get_text(" "))
                if txt:
                    out.append(txt)
            if out:
                return out
    return []

# RSS (병렬)
def _fetch_rss_one(url, limit_per_feed=60):
    out = []
    try:
        d = feedparser.parse(url)
        for e in d.entries[:limit_per_feed]:
            title = normalize_title(e.get("title"))
            if title and not is_noisy_title(title):
                out.append(title)
    except Exception:
        pass
    return out

def fetch_titles_from_rss(feeds, limit_per_feed=60, max_workers=6):
    if not feeds: return []
    results = []
    with ThreadPoolExecutor(max_workers=min(max_workers, len(feeds))) as ex:
        futs = {ex.submit(_fetch_rss_one, u, limit_per_feed): u for u in feeds}
        for f in as_completed(futs):
            try:
                res = f.result()
                if res: results.extend(res)
            except Exception:
                pass
    return results

# =========================
# 크롤링 실행
# =========================
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1366,768")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

titles_all = []
titles_by_source = defaultdict(list)

for src in SOURCES:
    try:
        titles = fetch_titles_by_selenium(
            driver, src["url"], src["selector"],
            wait=src.get("wait", 6), limit=src.get("limit", 80),
            source_name=src["name"], ua=src.get("ua"), headers=src.get("headers")
        )

        if not titles:
            titles = fetch_titles_by_requests(
                src["url"], src["selector"],
                encoding=src.get("encoding_fallback"),
                limit=src.get("limit", 80),
                headers=src.get("headers"),
                insecure_ok=src.get("insecure_ok", False)
            )

        titles = dedupe_keep_order(titles)
        titles_by_source[src["name"]].extend(titles)
        titles_all.extend(titles)
        print(f"[OK] {src['name']} 수집: {len(titles)}건")
    except Exception as e:
        print(f"[ERROR] {src['name']} 수집 실패: {e}")

# RSS
if USE_RSS:
    rss_titles = fetch_titles_from_rss(RSS_FEEDS, limit_per_feed=60, max_workers=6)
    titles_by_source["RSS"].extend(rss_titles)
    titles_all.extend(rss_titles)
    print(f"[OK] RSS 수집: {len(rss_titles)}건")

driver.quit()

titles_all = dedupe_keep_order(titles_all)
print(f"[INFO] 통합 텍스트 수(중복 제거 후): {len(titles_all)}")
if not titles_all:
    raise SystemExit("수집 실패: 소스/셀렉터/RSS 설정을 점검하세요.")

# =========================
# 형태소 분석 + n-gram
# =========================
okt = Okt()
nouns = []
for t in titles_all:
    nouns.extend(okt.nouns(t))

# 유니그램 카운트(원본)
counts_uni = Counter(nouns)

# 바이그램(연속 명사 붙이기) + 원본쌍 캐시
bigrams = Counter()
bigram_pair = {}  # "퇴사각" -> ("퇴사","각")
for title in titles_all:
    toks = [tok for tok in okt.nouns(title)]
    for i in range(len(toks)-1):
        left, right = toks[i], toks[i+1]
        bg = left + right
        if 2 <= len(bg) <= 12:
            bigrams[bg] += 1
            bigram_pair[bg] = (left, right)

# 최종 카운트(유니그램 + 바이그램 합산)
counts = Counter(counts_uni)
for k, v in bigrams.items():
    counts[k] += v

unique = list(counts.keys())
print("[INFO] 인식된 토큰 수(uni+bi):", len(unique))

# =========================
# 1차 규칙 필터
# =========================
def pre_filter(w):
    w = w.strip()
    if not w: return False
    if w in STOP: return False
    if ONLY_PUNCT.match(w): return False
    if EMOJI_RE.search(w): return False
    if REP_CHAR.search(w): return False
    if len(w) == 1 and not w.isalpha(): return False
    if KLOL_RE.match(w): return False
    return True

pre_candidates = [w for w in unique if pre_filter(w)]
print("[INFO] 1차 후보 개수:", len(pre_candidates))

# =========================
# 네이버 사전 조회(감점/회로차단/디스크캐시)
# =========================
STD_TTL_SEC = 86400
MAX_RETRIES = 4
BASE_BACKOFF = 0.6
BACKOFF_JITTER = 0.25
CB_WINDOW_SEC = 120
CB_FAIL_THRESHOLD = 5

CACHE_PATH = "naver_dict_cache.jsonl"
os.makedirs(os.path.dirname(CACHE_PATH) or ".", exist_ok=True)
_cache_lock = threading.Lock()
_disk_index = {}

def _load_cache_index():
    if not os.path.exists(CACHE_PATH): return
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                _disk_index[rec["word"]] = (rec["ok"], rec["expires_at"])
            except Exception: pass

def _append_cache(word, ok, ttl_sec=STD_TTL_SEC):
    expires_at = int(time.time()) + ttl_sec
    rec = {"word": word, "ok": ok, "expires_at": expires_at}
    with _cache_lock:
        with open(CACHE_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _disk_index[word] = (ok, expires_at)

_load_cache_index()

def _cache_get(word):
    v = _disk_index.get(word)
    if not v: return None
    ok, exp = v
    if time.time() > exp: return None
    return ok

_cb_state = {"open_until": 0, "fail_streak": 0}
def _cb_is_open(): return time.time() < _cb_state["open_until"]
def _cb_on_success(): _cb_state["fail_streak"] = 0
def _cb_on_failure():
    _cb_state["fail_streak"] += 1
    if _cb_state["fail_streak"] >= CB_FAIL_THRESHOLD:
        _cb_state["open_until"] = time.time() + CB_WINDOW_SEC

def _parse_is_standard(json_obj):
    try:
        m = json_obj.get("searchResultMap") or {}
        lm = m.get("searchResultListMap") or {}
        word = lm.get("WORD") or {}
        items = word.get("items") or []
        return len(items) > 0
    except Exception:
        return False

def is_standard_safe(word):
    c = _cache_get(word)
    if c is not None: return c
    if _cb_is_open():
        _append_cache(word, False, ttl_sec=60)
        return False
    url = NAVER_URL.format(q=word)
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=5)
            if r.status_code == 200:
                ok = _parse_is_standard(r.json())
                _append_cache(word, ok); _cb_on_success()
                return ok
            if r.status_code in (429,500,502,503,504):
                raise RuntimeError(f"Retryable HTTP {r.status_code}")
            _cb_on_failure(); _append_cache(word, False, ttl_sec=600)
            return False
        except (requests.Timeout, requests.ConnectionError, json.JSONDecodeError, RuntimeError) as e:
            last_err = str(e); _cb_on_failure()
            if attempt < MAX_RETRIES:
                backoff = BASE_BACKOFF * (2 ** (attempt - 1)) + (BACKOFF_JITTER * (attempt % 2))
                time.sleep(backoff)
            else:
                break
        except Exception as e:
            last_err = str(e); _cb_on_failure(); break
    _append_cache(word, False, ttl_sec=600)
    return False

# =========================
# 점수 구성요소
# =========================
def dice_score(bg):
    """바이그램 결합도(Dice). 0~1 근사."""
    if bg not in bigrams: return 0.0
    left, right = bigram_pair.get(bg, (None, None))
    if not left or not right: return 0.0
    a = counts_uni.get(left, 0)
    b = counts_uni.get(right, 0)
    ab = bigrams[bg]
    return (2.0 * ab) / (a + b + 1e-6)

def multi_source_hits(word):
    """여러 출처 동시 등장 수"""
    c = 0
    for titles in titles_by_source.values():
        found = False
        for t in titles:
            toks = set(okt.nouns(t))
            if word in toks or word in "".join(toks):
                found = True; break
        if found: c += 1
    return c

def source_weight_sum(word):
    s = 0.0
    for sname, titles in titles_by_source.items():
        if any(word in t for t in titles):
            s += SOURCE_WEIGHT.get(sname, 1.0)
    return max(1.0, s)

# 신규성/버스트 가점(이전 실행과 비교)
HIST_PATH = "counts_prev.json"
prev_counts = Counter()
if os.path.exists(HIST_PATH):
    try:
        prev_counts.update(json.load(open(HIST_PATH, "r", encoding="utf-8")))
    except Exception:
        pass

def novelty_boost(w):
    today = counts[w]
    prev  = prev_counts.get(w, 0)
    if prev == 0 and today >= 2:
        return 1.35
    growth = (today - prev) / (prev + 1)
    return min(1.0 + 0.2 * max(growth, 0), 1.6)

# 최종 스코어
def score(word):
    f = counts[word]
    base = math.log1p(f)
    boost = 1.0

    # 패턴
    if CHOSEONG_RE.match(word): boost *= 1.5
    if MIX_KO_EN.search(word):  boost *= 1.35
    if NUM_KO.search(word):     boost *= 1.2
    if REP_CHAR.search(word):   boost *= 0.6  # 도배성 억제

    # n-gram 가점
    if word in bigrams:
        d = min(1.0, dice_score(word))
        boost *= (1.0 + 0.4 * d)

    # 길이 보정
    L = len(word)
    if L == 1:        boost *= 0.6
    elif 2 <= L <= 6: boost *= 1.1
    elif L > 12:      boost *= 0.9

    # 사전 등재 감점(짧은 등재어는 강하게)
    if is_standard_safe(word):
        boost *= (0.35 if L <= 2 else 0.7)

    # 출처 가중치 + 다중출처
    sw = source_weight_sum(word)  # 1.0+
    boost *= (1.0 + 0.1 * (sw - 1.0))
    sh = multi_source_hits(word)
    if sh >= 2:
        boost *= (1.0 + 0.12 * (sh - 1))

    # 신규성/버스트
    boost *= novelty_boost(word)

    # 한글 포함 소폭 가점
    if HANGUL_RE.search(word):
        boost *= 1.05

    return base * boost

# 정렬
scored = sorted(pre_candidates, key=lambda w: (-score(w), -counts[w], w))

# 상·하위 2단계 선택
top  = scored[:TOP_STRICT_N]
tail = [w for w in scored[TOP_STRICT_N:TOP_STRICT_N+TAIL_POOL_N]]

def strict_keep(w):
    if is_standard_safe(w):             return False
    if len(w) == 1 and not w.isalpha(): return False
    if KLOL_RE.match(w):                return False
    if REP_CHAR.search(w):              return False
    return True

def soft_keep(w):
    if REP_CHAR.search(w):              return False
    if is_standard_safe(w):
        if CHOSEONG_RE.match(w) or MIX_KO_EN.search(w) or NUM_KO.search(w):
            return True
        return False
    return True

strict_list = [w for w in top if strict_keep(w)]
need = max(0, TARGET_N - len(strict_list))
if need > 0:
    tail_soft = [w for w in tail if soft_keep(w)]
    strict_list.extend(tail_soft[:need])

# 중복 제거
seen, final_list = set(), []
for w in strict_list:
    if w not in seen:
        seen.add(w)
        final_list.append(w)

print("\n[INFO] 통합 신조어 후보(LLM 전):")
for i, w in enumerate(final_list, 1):
    print(f"{i}. {w} (freq={counts.get(w,0)})")

# =========================
# LLM 최종 판별(선택)
# =========================
MIN_KEEP = 30  # 최소 개수 보장치

def ai_filter_neologisms(words, top_k=120):
    if not USE_LLM_FILTER or not words:
        return words  # LLM 미사용 시 그대로 반환

    words = words[:top_k]
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        system = "너는 한국어 신조어 감별기다. 반드시 JSON 배열만 출력하라."
        user = f"""
아래 단어들을 '신조어'|'일반어'|'고유명사'|'노이즈' 중 하나로 분류하되,
'신조어'와 '애매'만 골라 JSON 배열로 반환해. (배열 외 텍스트 절대 금지)
예시: ["단어1","단어2",...]

판정 가이드(완화):
- 2020년 이후 유행, 초성체/합성어/영+한 혼종/커뮤니티 은어는 가급적 포함
- 정치/뉴스 상시어는 제외

단어 목록: {", ".join(words)}
"""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            response_format={"type": "text"},  # JSON 배열 텍스트
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        )
        text = resp.choices[0].message.content.strip()
        try:
            data = json.loads(text)
            if isinstance(data, list) and all(isinstance(x, str) for x in data):
                return data
        except json.JSONDecodeError:
            print("[WARNING] JSON 파싱 실패 → 원본 사용")
        return words
    except Exception as e:
        print(f"[WARNING] LLM 필터 실패 → 원본 사용: {e}")
        return words

final_list_llm = ai_filter_neologisms(final_list, top_k=120)

# 최소 개수 보장(백필)
if not final_list_llm:
    final_list_llm = final_list[:MIN_KEEP]
elif len(final_list_llm) < MIN_KEEP:
    backfill = [w for w in final_list if w not in final_list_llm]
    final_list_llm = final_list_llm + backfill[:MIN_KEEP - len(final_list_llm)]

print(f"\n[DEBUG] LLM 전 후보 수: {len(final_list)}")
print(f"[DEBUG] LLM 후 후보 수: {len(final_list_llm)}")

# AI 필터 결과 기반 카운트 재계산
counts_llm = {w: counts.get(w, 0) for w in final_list_llm}

# 결과 출력
print("\n[OK] 최종 신조어 목록:")
for i, w in enumerate(final_list_llm, 1):
    print(f"{i}. {w} (freq={counts_llm[w]})")

# 다음 실행 비교용 카운트 저장
try:
    with open("counts_prev.json", "w", encoding="utf-8") as f:
        json.dump(dict(counts), f, ensure_ascii=False)
except Exception:
    pass

# =========================
# Firestore 저장
# =========================
def init_firestore():
    import os
    # 현재 스크립트의 디렉토리 기준으로 경로 설정
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(script_dir, "serviceAccountKey.json")
    cred = credentials.Certificate(cred_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    return firestore.client()

def save_neologisms_to_firestore(words, counts_obj):
    db = init_firestore()
    now = datetime.now(timezone.utc)
    ymd = now.astimezone().strftime("%Y-%m-%d")

    items = [{"word": w, "freq": int(counts_obj.get(w, 0))} for w in words]

    latest_ref = db.collection("neologisms").document("latest")
    latest_ref.set({
        "date": ymd,
        "updatedAt": now,
        "items": items,
    })

    day_ref = db.collection("neologisms").document(ymd)
    day_ref.set({
        "updatedAt": now,
        "items": items,
    })
    print(f"[OK] Firestore 저장 완료: {len(items)}건, 날짜={ymd}")

# Firebase로는 LLM 통과본만 전송(키 없으면 규칙 스코어본)
words_to_send = final_list_llm if final_list_llm else final_list
save_neologisms_to_firestore(words_to_send, counts)
