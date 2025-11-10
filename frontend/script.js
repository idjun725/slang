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
    
    // 신조어 검색 버튼
    document.getElementById('slang-search-btn').addEventListener('click', handleSlangSearch);
    
    // 검색 입력창에서 Enter 키 이벤트
    document.getElementById('slang-search-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleSlangSearch();
        }
    });
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
        // limit을 크게 설정하여 모든 신조어 가져오기
        const response = await fetch(`${API_BASE_URL}/ranking?limit=200`);
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
    
    // 사용 횟수 순으로 정렬 (백엔드에서 이미 정렬되어 오지만, 프론트엔드에서도 한 번 더)
    // 패턴 기반은 우선 표시하되, 동일 method 내에서는 usage_count 순
    const sortedRanking = [...ranking].sort((a, b) => {
        // 먼저 사용 횟수로 정렬 (내림차순)
        const countA = a.usage_count || 1;
        const countB = b.usage_count || 1;
        if (countA !== countB) {
            return countB - countA;  // 높은 순으로
        }
        // 사용 횟수가 같으면 패턴 기반 우선
        if (a.method === 'pattern' && b.method !== 'pattern') {
            return -1;
        }
        if (a.method !== 'pattern' && b.method === 'pattern') {
            return 1;
        }
        return 0;
    });
    
    rankingList.innerHTML = sortedRanking.map((item, index) => {
        const methodLabel = item.method === 'pattern' ? ' [패턴]' : '';
        const usageCount = item.usage_count || 1;
        
        return `
        <div class="ranking-item" data-word="${item.word}">
            <div class="rank">#${index + 1}</div>
            <div class="word-info">
                <div class="word">${item.word}${methodLabel}</div>
                <div class="meaning">${item.meaning || '의미 정보 없음'}</div>
                <div class="usage-count">사용 횟수: ${usageCount}회</div>
            </div>
        </div>
        `;
    }).join('');
}

// 특정 신조어의 영상 로드
async function loadVideosForWord(word) {
    const videoSection = document.getElementById(`videos-${word}`);
    const videoGrid = document.getElementById(`video-grid-${word}`);
    
    // 섹션 토글
    if (videoSection.classList.contains('active')) {
        videoSection.classList.remove('active');
        return;
    }
    
    videoSection.classList.add('active');
    videoGrid.innerHTML = '<div class="loading">영상을 불러오는 중...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/ranking/videos?word=${encodeURIComponent(word)}&limit=5`);
        const data = await response.json();
        
        if (data.success && data.videos && data.videos.length > 0) {
            displayVideos(videoGrid, data.videos, word);
        } else {
            // 에러 메시지가 있으면 표시, 없으면 기본 메시지
            const errorMessage = data.message || `'${word}' 키워드로 영상을 찾을 수 없습니다.`;
            videoGrid.innerHTML = `<div class="error">${errorMessage}</div>`;
            console.warn('영상 검색 결과:', data);
        }
    } catch (error) {
        console.error('Error loading videos:', error);
        videoGrid.innerHTML = '<div class="error">영상을 불러오는 데 실패했습니다. 서버 연결을 확인해주세요.</div>';
    }
}

// 신조어 검색 처리
async function handleSlangSearch() {
    const searchInput = document.getElementById('slang-search-input');
    const word = searchInput.value.trim();
    const searchResults = document.getElementById('search-results');
    
    if (!word) {
        alert('검색할 신조어를 입력해주세요.');
        return;
    }
    
    searchResults.style.display = 'block';
    searchResults.innerHTML = '<div class="loading">검색 중...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/slangs/search?word=${encodeURIComponent(word)}`);
        const data = await response.json();
        
        if (data.success) {
            displaySearchResult(data);
        } else {
            searchResults.innerHTML = `<div class="error">${data.message || '검색에 실패했습니다.'}</div>`;
        }
    } catch (error) {
        console.error('Error searching slang:', error);
        searchResults.innerHTML = '<div class="error">서버 연결에 실패했습니다.</div>';
    }
}

// 검색 결과 표시
function displaySearchResult(data) {
    const searchResults = document.getElementById('search-results');
    const result = data.data;
    
    let videosHTML = '';
    if (result.videos && result.videos.length > 0) {
        videosHTML = `
            <div class="search-result-videos">
                <h4>📹 관련 영상</h4>
                <div class="video-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px;">
                    ${result.videos.map(video => {
                        const youtubeUrl = `https://www.youtube.com/watch?v=${video.video_id}`;
                        return `
                            <div class="video-card" onclick="window.open('${youtubeUrl}', '_blank')" style="cursor: pointer; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                <img src="${video.thumbnail || ''}" alt="${video.title}" style="width: 100%; height: 120px; object-fit: cover;">
                                <div style="padding: 10px;">
                                    <div style="font-size: 0.85rem; font-weight: bold; margin-bottom: 5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${video.title || '제목 없음'}</div>
                                    <div style="font-size: 0.75rem; color: #666;">
                                        ${video.view_count ? formatNumber(video.view_count) + ' views' : ''}
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    } else {
        videosHTML = '<div class="search-result-videos"><h4>📹 관련 영상</h4><p style="color: #666;">영상을 찾을 수 없습니다.</p></div>';
    }
    
    let examplesHTML = '';
    if (result.examples && result.examples.length > 0) {
        examplesHTML = `
            <div class="search-result-examples">
                <h4>📝 사용 예문</h4>
                ${result.examples.map(example => `<div class="example-item">${example}</div>`).join('')}
            </div>
        `;
    } else {
        examplesHTML = '<div class="search-result-examples"><h4>📝 사용 예문</h4><p style="color: #666;">예문을 찾을 수 없습니다.</p></div>';
    }
    
    searchResults.innerHTML = `
        <div class="search-result-card">
            <div class="search-result-word">${result.word}</div>
            <div class="search-result-meaning">
                <strong>의미:</strong> ${result.meaning || '의미를 분석하는 중...'}
            </div>
            ${examplesHTML}
            ${videosHTML}
        </div>
    `;
}

// 영상 그리드 표시
function displayVideos(container, videos, word) {
    if (videos.length === 0) {
        container.innerHTML = '<div class="error">영상을 찾을 수 없습니다.</div>';
        return;
    }
    
    container.innerHTML = videos.map(video => {
        const youtubeUrl = `https://www.youtube.com/watch?v=${video.video_id}`;
        const matchCount = video.match_times ? video.match_times.length : 0;
        
        return `
            <div class="video-card" onclick="window.open('${youtubeUrl}', '_blank')">
                <img src="${video.thumbnail || ''}" alt="${video.title}" class="video-thumbnail" 
                     onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22112%22%3E%3Crect fill=%22%23ddd%22 width=%22200%22 height=%22112%22/%3E%3Ctext fill=%22%23999%22 x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22%3E썸네일 없음%3C/text%3E%3C/svg%3E'">
                <div class="video-info">
                    <div class="video-title">${video.title || '제목 없음'}</div>
                    <div class="video-meta">
                        ${video.view_count ? `조회수: ${formatNumber(video.view_count)}` : ''}
                        ${matchCount > 0 ? ` · ${matchCount}회 언급` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// 숫자 포맷팅 (예: 1000000 -> 100만)
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + '만';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k';
    }
    return num.toString();
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
