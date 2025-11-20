#!/usr/bin/env node
/**
 * Netlify 빌드 시 config.js 파일을 생성하는 스크립트
 * 환경변수 API_BASE_URL을 사용하여 config.js를 생성합니다.
 */
const fs = require('fs');
const path = require('path');

// 환경변수에서 API_BASE_URL 가져오기
const apiBaseUrl = process.env.API_BASE_URL || 'https://slang-production.up.railway.app';

// config.js 파일 내용 생성
const configContent = `// API URL 설정
// Netlify 환경변수에서 가져오거나, 기본값 사용
(function() {
    // Netlify 빌드 시 환경변수 주입
    if (typeof window !== 'undefined') {
        // 환경변수가 주입되지 않았으면 호스트명 기반으로 판단
        const hostname = window.location.hostname;
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            window.API_BASE_URL = 'http://localhost:8000';
        } else {
            // Netlify 환경변수에서 주입된 값 사용
            window.API_BASE_URL = '${apiBaseUrl}';
        }
    }
})();
`;

// config.js 파일 경로
const configPath = path.join(__dirname, 'config.js');

// 파일 쓰기
fs.writeFileSync(configPath, configContent, 'utf8');

console.log(`[빌드] config.js 생성 완료: API_BASE_URL=${apiBaseUrl}`);

