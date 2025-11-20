// API URL 설정
// Netlify 환경변수에서 가져오거나, 기본값 사용
(function() {
    // Netlify 빌드 시 환경변수 주입 (빌드 스크립트에서 처리)
    // 또는 런타임에 window 객체에 설정
    if (typeof window !== 'undefined') {
        // 환경변수가 주입되지 않았으면 호스트명 기반으로 판단
        const hostname = window.location.hostname;
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            window.API_BASE_URL = 'http://localhost:8000';
        } else {
            // Netlify 환경변수에서 가져오기 (빌드 시 주입 필요)
            // 또는 여기에 실제 백엔드 URL을 직접 입력
            window.API_BASE_URL = window.API_BASE_URL || 'https://slang-ko5f.onrender.com';
        }
    }
})();

