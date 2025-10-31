const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3000;

// 정적 파일 서빙
app.use(express.static(path.join(__dirname, 'dist')));

// 모든 라우트를 index.html로 리다이렉트 (SPA 지원)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`🚀 서버가 http://localhost:${PORT} 에서 실행 중입니다!`);
  console.log(`📱 다른 기기에서 접속하려면: http://[당신의IP]:${PORT}`);
});
