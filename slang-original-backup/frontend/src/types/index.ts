// 신조어 타입
export interface Slang {
  id: number
  word: string
  meaning: string
  usage_examples: string[]
  frequency: number
  rank: number
  rank_change: number
  category: string
  source: string
  first_seen: string
  last_updated: string
  trend_data?: TrendData[]
}

// 트렌드 데이터
export interface TrendData {
  date: string
  frequency: number
}

// 랭킹 필터
export interface RankingFilter {
  period: 'today' | 'week' | 'month'
  category?: string
}

// 사용자
export interface User {
  id: number
  email: string
  is_subscribed: boolean
  subscription_preferences: SubscriptionPreferences
  created_at: string
}

// 구독 설정
export interface SubscriptionPreferences {
  categories: string[]
  send_day: number // 0-6 (일-토)
  send_time: number // 0-23
}

// 뉴스레터
export interface Newsletter {
  id: number
  sent_date: string
  top_slangs: Slang[]
  open_count: number
  click_count: number
}

// API 응답
export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

// 페이지네이션
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}


