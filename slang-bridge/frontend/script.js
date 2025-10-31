const API_BASE_URL = 'http://localhost:8000';

// 세션 ID 가져오기
function getSessionId() {
    return localStorage.getItem('session_id');
}

// 로그인 체크
async function checkLogin() {
    const sessionId = getSessionId();
    if (!sessionId) {
        window.location.href = 'login.html';
        return null;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/me?session_id=${sessionId}`);
        const data = await response.json();
        
        if (data.success) {
            return data.user;
        } else {
            // 세션이 만료되었거나 유효하지 않음
            localStorage.removeItem('session_id');
            window.location.href = 'login.html';
            return null;
        }
    } catch (error) {
        console.error('Error checking login:', error);
        window.location.href = 'login.html';
        return null;
    }
}

// 페이지 로드 시 초기화
let currentUser = null;
document.addEventListener('DOMContentLoaded', async function() {
    // 로그인 체크
    currentUser = await checkLogin();
    if (!currentUser) return;
    
    // 사용자 정보 표시
    displayUserInfo(currentUser);
    
    // 구독 상태 로드
    loadSubscriptionStatus();
    
    // 랭킹 로드
    loadRanking();
    
    // 통계 로드
    loadStats();
    
    // 이벤트 리스너 설정
    setupEventListeners();
});

// 이벤트 리스너 설정
function setupEventListeners() {
    // 로그아웃 버튼
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    // 구독 토글
    document.getElementById('subscription-toggle').addEventListener('change', handleSubscriptionToggle);
}

// 사용자 정보 표시
function displayUserInfo(user) {
    document.getElementById('username-display').textContent = user.username;
}

// 로그아웃 처리
async function handleLogout() {
    const sessionId = getSessionId();
    
    try {
        if (sessionId) {
            await fetch(`${API_BASE_URL}/logout?session_id=${sessionId}`, {
                method: 'POST'
            });
        }
        
        // 로컬 스토리지에서 세션 ID 제거
        localStorage.removeItem('session_id');
        
        // 로그인 페이지로 이동
        window.location.href = 'login.html';
    } catch (error) {
        console.error('Error logging out:', error);
        // 에러가 나도 로그아웃 처리
        localStorage.removeItem('session_id');
        window.location.href = 'login.html';
    }
}

// 구독 상태 로드
async function loadSubscriptionStatus() {
    const sessionId = getSessionId();
    if (!sessionId) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/subscription/status?session_id=${sessionId}`);
        const data = await response.json();
        
        if (data.success !== undefined) {
            const toggle = document.getElementById('subscription-toggle');
            const statusText = document.getElementById('subscription-status');
            
            toggle.checked = data.subscribed;
            statusText.textContent = data.subscribed ? '✅ 구독 중' : '❌ 구독 안 함';
        }
    } catch (error) {
        console.error('Error loading subscription status:', error);
        document.getElementById('subscription-status').textContent = '구독 상태를 불러올 수 없습니다.';
    }
}

// 구독 토글 처리
async function handleSubscriptionToggle(event) {
    const sessionId = getSessionId();
    if (!sessionId) {
        event.target.checked = !event.target.checked; // 토글 되돌리기
        window.location.href = 'login.html';
        return;
    }
    
    const statusText = document.getElementById('subscription-status');
    statusText.textContent = '처리 중...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/subscription/toggle?session_id=${sessionId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusText.textContent = data.subscribed ? '✅ 구독 중' : '❌ 구독 안 함';
        } else {
            // 토글 되돌리기
            event.target.checked = !event.target.checked;
            statusText.textContent = data.detail || '구독 상태 변경에 실패했습니다.';
        }
    } catch (error) {
        console.error('Error toggling subscription:', error);
        // 토글 되돌리기
        event.target.checked = !event.target.checked;
        statusText.textContent = '서버 연결에 실패했습니다.';
    }
}

// 랭킹 로드
async function loadRanking() {
    try {
        const response = await fetch(`${API_BASE_URL}/ranking`);
        const data = await response.json();
        
        if (data.success) {
            displayRanking(data.data);
        } else {
            showError('랭킹을 불러올 수 없습니다.');
        }
    } catch (error) {
        console.error('Error loading ranking:', error);
        showError('서버 연결에 실패했습니다.');
    }
}

// 랭킹 표시
function displayRanking(ranking) {
    const rankingList = document.getElementById('ranking-list');
    
    if (ranking.length === 0) {
        rankingList.innerHTML = '<div class="loading">아직 신조어가 없습니다. 크롤링을 실행해보세요!</div>';
        return;
    }
    
    rankingList.innerHTML = ranking.map((item, index) => `
        <div class="ranking-item">
            <div class="rank">#${index + 1}</div>
            <div class="word-info">
                <div class="word">${item.word}</div>
                <div class="meaning">${item.meaning || '의미 정보 없음'}</div>
                <div class="usage-count">사용 횟수: ${item.usage_count}회</div>
            </div>
        </div>
    `).join('');
}

// 통계 로드
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const data = await response.json();
        
        if (data.success) {
            displayStats(data.data);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// 통계 표시
function displayStats(stats) {
    const statsContainer = document.getElementById('stats');
    statsContainer.innerHTML = `
        <div class="stat-item">
            <div class="stat-number">${stats.total_slangs}</div>
            <div class="stat-label">총 신조어</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">${stats.total_subscribers}</div>
            <div class="stat-label">구독자</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">${stats.recent_slangs}</div>
            <div class="stat-label">최근 추가</div>
        </div>
    `;
}

// 에러 메시지 표시
function showError(message) {
    const rankingList = document.getElementById('ranking-list');
    rankingList.innerHTML = `<div class="error">${message}</div>`;
}
