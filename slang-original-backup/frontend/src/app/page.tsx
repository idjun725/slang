import Link from 'next/link'
import { TrendingUp, Mail, Search, Users } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-8 w-8 text-primary-600" />
              <span className="text-2xl font-bold text-gray-900">슬랭 브릿지</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/ranking"
                className="text-gray-700 hover:text-primary-600 transition"
              >
                랭킹
              </Link>
              <Link
                href="/dictionary"
                className="text-gray-700 hover:text-primary-600 transition"
              >
                사전
              </Link>
              <Link
                href="/newsletter"
                className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition"
              >
                뉴스레터 구독
              </Link>
            </div>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            세대 간 소통을 연결하는
            <br />
            <span className="text-primary-600">신조어 학습 플랫폼</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            디시인사이드에서 실시간으로 수집한 최신 신조어를
            <br />
            쉽고 빠르게 이해하세요
          </p>
          <div className="flex justify-center space-x-4">
            <Link
              href="/ranking"
              className="bg-primary-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-primary-700 transition shadow-lg"
            >
              신조어 랭킹 보기
            </Link>
            <Link
              href="/newsletter"
              className="bg-white text-primary-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-50 transition shadow-lg border-2 border-primary-600"
            >
              무료 구독하기
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mt-20">
          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-6">
              <TrendingUp className="h-8 w-8 text-primary-600" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              실시간 랭킹
            </h3>
            <p className="text-gray-600">
              디시인사이드 게시물을 분석하여 가장 많이 사용되는 신조어를 실시간으로 제공합니다.
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-6">
              <Mail className="h-8 w-8 text-primary-600" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              주간 뉴스레터
            </h3>
            <p className="text-gray-600">
              매주 월요일, 지난 주 가장 인기 있었던 신조어 TOP 5를 이메일로 받아보세요.
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-6">
              <Search className="h-8 w-8 text-primary-600" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              신조어 사전
            </h3>
            <p className="text-gray-600">
              궁금한 신조어를 검색하고, 의미와 사용 예시를 쉽게 찾아보세요.
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-20 bg-white rounded-xl shadow-lg p-12">
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-primary-600 mb-2">1,234</div>
              <div className="text-gray-600">수집된 신조어</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary-600 mb-2">5,678</div>
              <div className="text-gray-600">구독자</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary-600 mb-2">매시간</div>
              <div className="text-gray-600">업데이트</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary-600 mb-2">무료</div>
              <div className="text-gray-600">평생 사용</div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <TrendingUp className="h-6 w-6 text-primary-600" />
                <span className="text-xl font-bold text-gray-900">슬랭 브릿지</span>
              </div>
              <p className="text-gray-600">
                세대 간 소통을 위한 신조어 학습 플랫폼
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">서비스</h4>
              <ul className="space-y-2 text-gray-600">
                <li><Link href="/ranking">신조어 랭킹</Link></li>
                <li><Link href="/dictionary">신조어 사전</Link></li>
                <li><Link href="/newsletter">뉴스레터</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">문의</h4>
              <ul className="space-y-2 text-gray-600">
                <li>contact@slangbridge.com</li>
                <li>개인정보처리방침</li>
                <li>이용약관</li>
              </ul>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t text-center text-gray-500">
            © 2025 슬랭 브릿지. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}


