import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'
import { Providers } from '@/components/Providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: '슬랭 브릿지 - 세대 간 소통을 위한 신조어 학습 플랫폼',
  description: '디시인사이드 기반 실시간 신조어 랭킹 및 주간 뉴스레터 서비스',
  keywords: ['신조어', '세대 간 소통', '언어 학습', 'MZ세대', '디시인사이드'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}


