import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import List, Dict

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.username = os.getenv('GMAIL_USER', '')
        self.password = os.getenv('GMAIL_PASS', '')
    
    def send_newsletter(self, subscribers: List[str], top_slangs: List[Dict]) -> bool:
        """뉴스레터 발송"""
        if not self.username or not self.password:
            print("Gmail 계정 정보가 설정되지 않았습니다.")
            return False
        
        try:
            # 이메일 내용 생성
            subject = "📱 주간 신조어 랭킹 - 세대 간 소통의 다리"
            
            html_content = self._create_html_content(top_slangs)
            text_content = self._create_text_content(top_slangs)
            
            # SMTP 연결
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            
            # 각 구독자에게 발송
            success_count = 0
            for email in subscribers:
                try:
                    msg = MIMEMultipart('alternative')
                    msg['From'] = self.username
                    msg['To'] = email
                    msg['Subject'] = subject
                    
                    msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
                    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
                    
                    server.send_message(msg)
                    success_count += 1
                    print(f"[OK] {email} 발송 완료")
                    
                except Exception as e:
                    print(f"[ERROR] {email} 발송 실패: {e}")
            
            server.quit()
            print(f"뉴스레터 발송 완료: {success_count}/{len(subscribers)}")
            return success_count > 0
            
        except Exception as e:
            print(f"뉴스레터 발송 실패: {e}")
            return False
    
    def _create_html_content(self, top_slangs: List[Dict]) -> str:
        """HTML 이메일 내용 생성"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>주간 신조어 랭킹</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #4CAF50; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f9f9f9; }
                .slang-item { background: white; margin: 10px 0; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
                .rank { font-size: 24px; font-weight: bold; color: #4CAF50; }
                .word { font-size: 18px; font-weight: bold; margin: 5px 0; }
                .meaning { color: #666; margin: 5px 0; }
                .examples { color: #888; font-style: italic; }
                .footer { text-align: center; padding: 20px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📱 주간 신조어 랭킹</h1>
                    <p>세대 간 소통의 다리</p>
                </div>
                <div class="content">
                    <h2>이번 주 TOP 5 신조어</h2>
        """
        
        for i, slang in enumerate(top_slangs[:5], 1):
            examples_text = ", ".join(slang.get('examples', [])[:3])
            html += f"""
                    <div class="slang-item">
                        <div class="rank">#{i}</div>
                        <div class="word">{slang['word']}</div>
                        <div class="meaning">{slang.get('meaning', '의미 정보 없음')}</div>
                        <div class="examples">예시: {examples_text if examples_text else '예시 없음'}</div>
                    </div>
            """
        
        html += """
                </div>
                <div class="footer">
                    <p>구독 해지: <a href="http://localhost:8001/unsubscribe.html">여기를 클릭하세요</a></p>
                    <p>© 2024 Slang Bridge. 모든 권리 보유.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _create_text_content(self, top_slangs: List[Dict]) -> str:
        """텍스트 이메일 내용 생성"""
        text = "📱 주간 신조어 랭킹 - 세대 간 소통의 다리\n\n"
        text += "이번 주 TOP 5 신조어\n"
        text += "=" * 30 + "\n\n"
        
        for i, slang in enumerate(top_slangs[:5], 1):
            examples_text = ", ".join(slang.get('examples', [])[:3])
            text += f"#{i} {slang['word']}\n"
            text += f"의미: {slang.get('meaning', '의미 정보 없음')}\n"
            text += f"예시: {examples_text if examples_text else '예시 없음'}\n"
            text += "-" * 20 + "\n\n"
        
        text += "구독 해지: http://localhost:8001/unsubscribe.html\n"
        text += "© 2024 Slang Bridge. 모든 권리 보유."
        
        return text

