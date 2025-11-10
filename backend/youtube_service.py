"""
YouTube API를 사용한 영상 검색 및 자막 분석 서비스
"""
import os
import re
import json
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False
    print("[WARNING] google-api-python-client not installed. YouTube features will be disabled.")

# 환경변수 로드
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)

class YouTubeService:
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY', '')
        
        if not YOUTUBE_API_AVAILABLE:
            self.youtube = None
            print("[YouTube] google-api-python-client library not installed.")
        elif not self.api_key:
            self.youtube = None
            print("[YouTube] API key not found. Set YOUTUBE_API_KEY in .env file.")
        else:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
                print("[YouTube] API 초기화 성공")
            except Exception as e:
                self.youtube = None
                print(f"[YouTube] API 초기화 실패: {e}")
    
    def search_shorts_by_keyword(self, keyword: str, max_results: int = 10) -> List[Dict]:
        """키워드로 YouTube Shorts 영상 검색"""
        if not self.youtube:
            return []
        
        try:
            # 여러 검색 시도: #shorts 포함 검색 → 일반 검색
            search_queries = [
                f'{keyword} #shorts',
                f'{keyword} 쇼츠',
                keyword  # 마지막으로 키워드만
            ]
            
            all_videos = []
            seen_ids = set()
            
            for query in search_queries:
                if len(all_videos) >= max_results:
                    break
                    
                try:
                    # 먼저 Shorts 검색 시도
                    request = self.youtube.search().list(
                        part='snippet',
                        q=query,
                        type='video',
                        videoDuration='short',  # 4분 이하
                        maxResults=max_results * 2,
                        order='relevance'
                    )
                    
                    response = request.execute()
                    
                    for item in response.get('items', []):
                        video_id = item['id']['videoId']
                        if video_id in seen_ids:
                            continue
                        seen_ids.add(video_id)
                        
                        snippet = item['snippet']
                        
                        all_videos.append({
                            'video_id': video_id,
                            'title': snippet['title'],
                            'description': snippet['description'],
                            'thumbnail': snippet['thumbnails']['high']['url'],
                            'channel_title': snippet['channelTitle'],
                            'published_at': snippet['publishedAt']
                        })
                        
                        if len(all_videos) >= max_results:
                            break
                    
                    # Shorts 검색에서 충분히 찾지 못했으면 일반 영상도 검색
                    if len(all_videos) < max_results and query == search_queries[-1]:
                        print(f"[YouTube] Shorts 검색으로 부족 ({len(all_videos)}개), 일반 영상도 검색 시도...")
                        try:
                            general_request = self.youtube.search().list(
                                part='snippet',
                                q=keyword,
                                type='video',
                                maxResults=max_results * 2,
                                order='relevance'
                            )
                            general_response = general_request.execute()
                            
                            for item in general_response.get('items', []):
                                video_id = item['id']['videoId']
                                if video_id in seen_ids:
                                    continue
                                seen_ids.add(video_id)
                                
                                snippet = item['snippet']
                                all_videos.append({
                                    'video_id': video_id,
                                    'title': snippet['title'],
                                    'description': snippet['description'],
                                    'thumbnail': snippet['thumbnails']['high']['url'],
                                    'channel_title': snippet['channelTitle'],
                                    'published_at': snippet['publishedAt']
                                })
                                
                                if len(all_videos) >= max_results:
                                    break
                        except Exception as e:
                            print(f"[YouTube] 일반 영상 검색 실패: {e}")
                            continue
                            
                except HttpError as e:
                    if 'quota' in str(e).lower():
                        print(f"[YouTube] 할당량 초과: {e}")
                        break
                    print(f"[YouTube] 검색 쿼리 '{query}' 실패: {e}")
                    continue
                except Exception as e:
                    print(f"[YouTube] 검색 오류: {e}")
                    continue
            
            print(f"[YouTube] 검색 완료: {len(all_videos)}개 영상 발견")
            return all_videos[:max_results]
        
        except HttpError as e:
            error_msg = str(e)
            if 'quota' in error_msg.lower():
                print(f"[YouTube] API 할당량 초과")
            else:
                print(f"[YouTube] 검색 오류: {e}")
            return []
        except Exception as e:
            print(f"[YouTube] 검색 실패: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """비디오 상세 정보 조회 (조회수, 좋아요 등)"""
        if not self.youtube or not video_ids:
            return []
        
        try:
            # 한 번에 최대 50개까지 조회 가능
            video_ids_str = ','.join(video_ids[:50])
            
            request = self.youtube.videos().list(
                part='statistics,contentDetails',
                id=video_ids_str
            )
            
            response = request.execute()
            details = []
            
            for item in response.get('items', []):
                video_id = item['id']
                stats = item.get('statistics', {})
                content = item.get('contentDetails', {})
                
                # ISO 8601 기간 형식을 초로 변환
                duration = self._parse_duration(content.get('duration', 'PT0S'))
                
                details.append({
                    'video_id': video_id,
                    'view_count': int(stats.get('viewCount', 0)),
                    'like_count': int(stats.get('likeCount', 0)),
                    'duration': duration
                })
            
            return details
        
        except HttpError as e:
            print(f"[YouTube] 상세 정보 조회 오류: {e}")
            return []
        except Exception as e:
            print(f"[YouTube] 상세 정보 조회 실패: {e}")
            return []
    
    def _parse_duration(self, duration_str: str) -> int:
        """ISO 8601 기간을 초로 변환 (예: PT1M30S -> 90)"""
        import re
        pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = pattern.match(duration_str)
        
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def get_video_captions(self, video_id: str, language: str = 'ko') -> Optional[str]:
        """영상의 자막 다운로드"""
        if not self.youtube:
            return None
        
        try:
            # 1. 자막 트랙 목록 가져오기
            captions_request = self.youtube.captions().list(
                part='snippet',
                videoId=video_id
            )
            
            captions_response = captions_request.execute()
            caption_tracks = captions_response.get('items', [])
            
            if not caption_tracks:
                return None
            
            # 한국어 자막 찾기
            caption_id = None
            for track in caption_tracks:
                track_lang = track['snippet'].get('language', '')
                # 한국어 또는 영어 자막 우선
                if track_lang == language:
                    caption_id = track['id']
                    break
            
            # 한국어 자막이 없으면 영어 자막 찾기
            if not caption_id:
                for track in caption_tracks:
                    if track['snippet'].get('language', '').startswith('en'):
                        caption_id = track['id']
                        break
            
            # 그래도 없으면 첫 번째 자막 사용
            if not caption_id:
                caption_id = caption_tracks[0]['id']
            
            # 2. 자막 다운로드
            download_request = self.youtube.captions().download(
                id=caption_id,
                tfmt='srt'  # SRT 형식
            )
            
            # 자막 내용 다운로드
            caption_text = download_request.execute()
            
            # 바이트 데이터를 문자열로 변환
            if isinstance(caption_text, bytes):
                return caption_text.decode('utf-8')
            elif isinstance(caption_text, str):
                return caption_text
            else:
                return str(caption_text)
        
        except HttpError as e:
            if e.resp.status == 404:
                # 자막이 없음 (정상적인 경우)
                return None
            elif e.resp.status == 403:
                print(f"[YouTube] 자막 접근 권한 없음 ({video_id}): {e}")
                return None
            else:
                print(f"[YouTube] 자막 다운로드 오류 ({video_id}): {e}")
                return None
        except Exception as e:
            # 자막 다운로드 실패는 치명적이지 않음 (로그만 출력)
            return None
    
    def parse_srt(self, srt_text: str) -> List[Dict]:
        """SRT 자막 파일 파싱"""
        import re
        
        # SRT 블록 패턴
        pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\d+\n|\Z)', re.DOTALL)
        
        captions = []
        for match in pattern.finditer(srt_text):
            start_time = self._srt_time_to_seconds(match.group(2))
            end_time = self._srt_time_to_seconds(match.group(3))
            text = match.group(4).strip().replace('\n', ' ')
            
            captions.append({
                'start': start_time,
                'end': end_time,
                'text': text
            })
        
        return captions
    
    def _srt_time_to_seconds(self, time_str: str) -> float:
        """SRT 시간 형식을 초로 변환 (예: 00:01:30,500 -> 90.5)"""
        time_part, ms_part = time_str.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)
        
        return h * 3600 + m * 60 + s + ms / 1000.0
    
    def find_slang_in_captions(self, captions: List[Dict], slang_word: str) -> List[float]:
        """자막에서 신조어가 등장하는 시간 위치 찾기"""
        match_times = []
        
        for caption in captions:
            text = caption['text']
            
            # 대소문자 구분 없이 검색
            if slang_word.lower() in text.lower():
                # 해당 자막의 시작 시간 추가
                match_times.append(caption['start'])
        
        return match_times
    
    def find_videos_with_slang(self, slang_word: str, max_results: int = 5) -> List[Dict]:
        """신조어가 포함된 영상 찾기 (검색 + 자막 분석)
        
        자막이 없는 영상도 포함시키되, 자막에서 단어를 찾은 영상은 우선순위를 높입니다.
        """
        if not self.youtube:
            print(f"[YouTube] API 미설정 - '{slang_word}' 검색 불가")
            return []
        
        print(f"[YouTube] '{slang_word}' 검색 중...")
        
        # 1. 영상 검색
        videos = self.search_shorts_by_keyword(slang_word, max_results=max_results * 3)
        
        if not videos:
            print(f"[YouTube] '{slang_word}' 검색 결과 없음")
            return []
        
        print(f"[YouTube] {len(videos)}개 영상 검색됨")
        
        # 2. 영상 상세 정보 조회
        video_ids = [v['video_id'] for v in videos]
        details = self.get_video_details(video_ids)
        
        # 상세 정보를 비디오 정보에 병합
        details_dict = {d['video_id']: d for d in details}
        for video in videos:
            video_id = video['video_id']
            if video_id in details_dict:
                video.update(details_dict[video_id])
        
        # 3. 제목에 키워드가 있는지 먼저 확인
        title_matched_videos = []
        other_videos = []
        
        for video in videos:
            title = video.get('title', '').lower()
            description = video.get('description', '').lower()
            keyword_lower = slang_word.lower()
            
            # 제목이나 설명에 키워드가 있으면 우선순위 높임
            if keyword_lower in title or keyword_lower in description:
                title_matched_videos.append(video)
            else:
                other_videos.append(video)
        
        print(f"[YouTube] 제목 매칭: {len(title_matched_videos)}개, 기타: {len(other_videos)}개")
        
        # 4. 각 영상의 자막 분석 (제목 매칭 영상 우선)
        matched_videos = []  # 자막에서 단어 발견한 영상
        caption_checked_videos = []  # 자막 체크했지만 없는 영상
        
        # 제목 매칭 영상 먼저 처리
        for video in title_matched_videos + other_videos:
            if len(matched_videos) + len(caption_checked_videos) >= max_results * 2:
                break
                
            video_id = video['video_id']
            
            # 자막 다운로드 (시도)
            caption_text = None
            try:
                caption_text = self.get_video_captions(video_id)
            except Exception as e:
                print(f"[YouTube] 자막 다운로드 실패 ({video_id}): {e}")
            
            if caption_text:
                try:
                    # SRT 파싱
                    captions = self.parse_srt(caption_text)
                    
                    # 신조어 검색
                    match_times = self.find_slang_in_captions(captions, slang_word)
                    
                    if match_times:
                        video['match_times'] = match_times
                        matched_videos.append(video)
                        print(f"[YouTube] '{slang_word}' 발견 (자막): {video['title']} ({len(match_times)}회)")
                    else:
                        # 자막은 있지만 단어가 없는 경우도 포함
                        video['match_times'] = []
                        caption_checked_videos.append(video)
                except Exception as e:
                    print(f"[YouTube] 자막 파싱 실패 ({video_id}): {e}")
                    # 파싱 실패해도 영상은 포함
                    video['match_times'] = []
                    caption_checked_videos.append(video)
            else:
                # 자막이 없는 영상도 포함 (제목에 단어가 있을 수 있음)
                video['match_times'] = []
                caption_checked_videos.append(video)
            
            # API 호출 제한을 위한 대기
            time.sleep(0.1)
            
            # 충분한 영상을 찾으면 중단 (자막 매칭 영상 기준)
            if len(matched_videos) >= max_results:
                break
        
        # 결과: 자막에서 찾은 영상을 우선으로, 부족하면 제목 매칭 영상, 그 다음 일반 영상
        result = matched_videos[:max_results]
        
        if len(result) < max_results:
            # 제목 매칭 영상 추가 (자막 매칭과 중복 제거)
            matched_ids = {v['video_id'] for v in matched_videos}
            for video in title_matched_videos:
                if len(result) >= max_results:
                    break
                if video['video_id'] not in matched_ids:
                    result.append(video)
        
        if len(result) < max_results:
            # 부족하면 일반 영상 추가
            matched_ids = {v['video_id'] for v in result}
            remaining = max_results - len(result)
            for video in caption_checked_videos:
                if len(result) >= max_results:
                    break
                if video['video_id'] not in matched_ids:
                    result.append(video)
                    remaining -= 1
                    if remaining <= 0:
                        break
        
        print(f"[YouTube] '{slang_word}' 최종 결과: {len(result)}개 영상 (자막 매칭: {len(matched_videos)}개, 제목 매칭: {len(title_matched_videos)}개)")
        return result[:max_results]

