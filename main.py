import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import json
import re
from typing import List, Dict, Optional
import calendar as cal
import time

# 로컬 모듈 import
from database import *
from ai_models import AIModelManager

# ✅ 페이지 설정 (layout="centered"로 수정)
st.set_page_config(
    page_title="마음톡 - 나만의 감정일기", 
    page_icon="💜", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# ✅ 상수 설정
APP_PASSWORD = "2752"
MAX_FREE_TOKENS = 100000
HARMFUL_KEYWORDS = [
    "자살", "죽고싶다", "죽고 싶다", "자살하고", "자해", "손목", "극단적", "생을 마감",
    "죽고 싶어", "사라지고 싶다", "끝내고 싶다", "힘들어서 죽을", "죽어버리고", 
    "죽었으면", "살기 싫다", "살고 싶지", "베고 싶다", "목 매달아"
]

VIOLENCE_KEYWORDS = [
    "때리고 싶다", "죽이고 싶다", "칼", "총", "성폭행", "강간", "폭행", "때렸다",
    "맞았다", "협박", "폭력", "성추행", "칼로 찌르", "총으로 쏘"
]

# ✅ 기본 AI 이름 설정
DEFAULT_AI_NAME = "루나"
RECOMMENDED_AI_NAMES = ["루나", "별이", "하늘이", "민트", "소라", "유나"]

# ✅ 테마 색상 설정
THEMES = {
    "핑크": {
        "background": "linear-gradient(135deg, #fefefe 0%, #faf9f7 100%)",
        "button_bg": "linear-gradient(135deg, #ffeef0 0%, #ffe4e6 100%)",
        "button_hover": "linear-gradient(135deg, #ffd7dc 0%, #ffb3ba 100%)",
        "button_text": "#8e4b5a",
        "shadow": "rgba(255, 182, 193, 0.3)"
    },
    "블루": {
        "background": "linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%)",
        "button_bg": "linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)",
        "button_hover": "linear-gradient(135deg, #90caf9 0%, #64b5f6 100%)",
        "button_text": "#1565c0",
        "shadow": "rgba(33, 150, 243, 0.3)"
    },
    "그린": {
        "background": "linear-gradient(135deg, #f1f8e9 0%, #e8f5e8 100%)",
        "button_bg": "linear-gradient(135deg, #e8f5e8 0%, #c8e6c8 100%)",
        "button_hover": "linear-gradient(135deg, #a5d6a7 0%, #81c784 100%)",
        "button_text": "#2e7d32",
        "shadow": "rgba(76, 175, 80, 0.3)"
    },
    "라벤더": {
        "background": "linear-gradient(135deg, #faf9fc 0%, #f3e5f5 100%)",
        "button_bg": "linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%)",
        "button_hover": "linear-gradient(135deg, #ce93d8 0%, #ba68c8 100%)",
        "button_text": "#7b1fa2",
        "shadow": "rgba(156, 39, 176, 0.3)"
    }
}

# 데이터베이스 초기화
init_database()

# AI 모델 매니저 초기화
@st.cache_resource
def get_ai_model():
    return AIModelManager()

# ✅ 세션 상태 초기화
def init_session_state():
    """세션 상태 초기화 (SQLite 데이터 복원 포함)"""
    defaults = {
        "authenticated": False,
        "current_step": "mood_selection",
        "current_mood": None,
        "chat_messages": [],
        "diary_entries": [],
        "conversation_context": [],
        "token_usage": 0,
        "deleted_entries": [],
        "temp_diary_data": {},
        "ai_name": DEFAULT_AI_NAME,
        "ai_typing": False,
        "menu_option": "🏠 홈",
        "selected_theme": "라벤더",
        "consecutive_days": 0,
        "last_entry_date": None,
        "app_initialized": True
    }
    
    # 먼저 기본값 설정
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    # SQLite에서 데이터 복원
    load_data_from_db()
    
    # 데이터 타입 검증 및 복구
    for key, default_value in defaults.items():
        try:
            if key == "diary_entries" and not isinstance(st.session_state[key], list):
                st.session_state[key] = []
            elif key == "deleted_entries" and not isinstance(st.session_state[key], list):
                st.session_state[key] = []
            elif key == "token_usage" and not isinstance(st.session_state[key], (int, float)):
                st.session_state[key] = 0
        except Exception as e:
            st.session_state[key] = default_value

# ✅ 테마별 스타일 생성 함수
def get_theme_style(theme_name):
    theme = THEMES.get(theme_name, THEMES["라벤더"])
    
    return f"""
    <style>
    .stApp {{
        background: {theme['background']} !important;
    }}
    
    .main .block-container {{
        background: transparent !important;
        padding-bottom: 80px !important;
    }}
    
    .stButton > button {{
        border-radius: 20px !important;
        border: none !important;
        padding: 1rem !important;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        height: 200px !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        white-space: pre-line !important;
        box-shadow: 0 4px 15px {theme['shadow']} !important;
        text-align: center !important;
        cursor: pointer !important;
        background: {theme['button_bg']} !important;
        color: {theme['button_text']} !important;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-5px) !important;
        box-shadow: 0 10px 30px {theme['shadow']} !important;
        background: {theme['button_hover']} !important;
    }}
    
    .stButton > button:active {{
        transform: translateY(-2px) !important;
    }}
    
    .main-header {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        font-size: 18px;
    }}
    .main-header h1 {{
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
    }}
    .chat-container {{
        background: white;
        border: 2px solid #e3f2fd;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        min-height: 400px;
        font-size: 16px;
    }}
    .ai-message {{
        background: linear-gradient(135deg, #ffeef0 0%, #ffe4e6 100%);
        padding: 1.2rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 4px solid #ff69b4;
        font-size: 16px;
        text-align: left;
    }}
    .user-message {{
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
        padding: 1.2rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 4px solid #2196f3;
        text-align: left;
        font-size: 16px;
    }}
    .warning-box {{
        background: linear-gradient(135deg, #ffebee 0%, #fce4ec 100%);
        border: 2px solid #f44336;
        color: #c62828;
        padding: 1.8rem;
        border-radius: 15px;
        margin: 1rem 0;
        font-size: 16px;
    }}
    .summary-box {{
        background: linear-gradient(135deg, #fff3e0 0%, #fce4ec 100%);
        border: 2px solid #ff9800;
        padding: 1.8rem;
        border-radius: 15px;
        margin: 1rem 0;
        font-size: 16px;
    }}
    .token-bar {{
        background: #f0f0f0;
        border-radius: 20px;
        padding: 8px;
        margin: 12px 0;
        font-size: 15px;
    }}
    .footer {{
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: rgba(248, 249, 250, 0.95);
        color: #6c757d;
        text-align: center;
        padding: 12px 20px;
        font-size: 12px;
        border-top: 1px solid #dee2e6;
        backdrop-filter: blur(10px);
        z-index: 999;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    }}
    .stSelectbox label, .stTextArea label, .stButton button {{
        font-size: 16px !important;
    }}
    .stTextArea textarea {{
        font-size: 16px !important;
    }}
    .stSelectbox div {{
        font-size: 16px !important;
    }}
    </style>
    """

# ✅ 유틸리티 함수들
def get_korean_postposition(name):
    """한글 이름 뒤에 오는 조사 '이'/'가'를 결정합니다."""
    if not name:
        return "가"
    last_char = name[-1]
    # 한글 음절의 유니코드 범위: 0xAC00 ~ 0xD7A3
    if '가' <= last_char <= '힣':
        # 마지막 글자의 종성(받침) 유무 확인
        has_jongseong = (ord(last_char) - 0xAC00) % 28 > 0
        return "이가" if has_jongseong else "가"
    else:
        # 한글이 아닌 경우 '가'를 기본으로 사용
        return "가"

def check_harmful_content(text: str) -> bool:
    """유해 콘텐츠 검사"""
    if not text or not isinstance(text, str):
        return False
    
    try:
        text_lower = text.lower().replace(" ", "")
        harmful_patterns = [
            "자살", "죽고싶", "자해", "죽고싶어", "사라지고싶", "끝내고싶", 
            "살기싫", "살고싶지", "죽어버리", "죽었으면", "베고싶", "자살하고"
        ]
        
        return any(pattern in text_lower for pattern in harmful_patterns)
    except Exception:
        return False

def check_violence_content(text: str) -> bool:
    """폭력 콘텐츠 검사"""
    if not text or not isinstance(text, str):
        return False
    
    try:
        text_lower = text.lower().replace(" ", "")
        violence_patterns = [
            "때리고싶", "죽이고싶", "칼", "총", "성폭행", "강간", "폭행", 
            "때렸다", "맞았다", "협박", "폭력", "성추행"
        ]
        
        return any(pattern in text_lower for pattern in violence_patterns)
    except Exception:
        return False

def display_token_bar():
    """토큰 사용량 표시 (로컬 모델이므로 항상 충분함)"""
    try:
        # 로컬 모델 사용으로 무제한이지만 UI 유지
        token_usage = max(0, int(st.session_state.get('token_usage', 0)))
        max_tokens = MAX_FREE_TOKENS
        
        # 항상 충분한 상태로 표시
        color = "#4CAF50"
        status = "무제한 (로컬 모델)"
        
        st.markdown(f"""
        <div class="token-bar">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                <span style="font-size: 14px; font-weight: bold;">💫 AI와 대화할 수 있는 에너지</span>
                <span style="font-size: 12px; color: #666;">무제한 사용 가능</span>
            </div>
            <div style="background: #e0e0e0; height: 8px; border-radius: 10px;">
                <div style="background: {color}; width: 100%; height: 100%; border-radius: 10px;"></div>
            </div>
            <div style="text-align: center; font-size: 12px; color: {color}; margin-top: 5px;">
                상태: {status}
            </div>
        </div>
        """, unsafe_allow_html=True)
    except Exception:
        pass

def calculate_consecutive_days():
    """연속 작성일 계산 (중복 날짜 제거 로직 수정)"""
    try:
        if not st.session_state.diary_entries:
            return 0
        
        # 일기를 작성한 날짜만 추출하여 중복을 제거합니다.
        entry_dates = {datetime.strptime(entry['date'], '%Y-%m-%d').date() 
                      for entry in st.session_state.diary_entries if 'date' in entry}
        
        if not entry_dates:
            return 0
        
        # 날짜를 최신순으로 정렬합니다.
        sorted_dates = sorted(list(entry_dates), reverse=True)
        
        today = datetime.now().date()
        
        # 오늘 일기를 썼는지, 어제 썼는지에 따라 시작점을 정합니다.
        if today not in sorted_dates:
            # 오늘 일기를 안 썼다면, 어제부터 연속인지 확인합니다.
            start_date = today - timedelta(days=1)
            consecutive = 0
        else:
            # 오늘 일기를 썼다면, 오늘부터 연속인지 확인합니다.
            start_date = today
            consecutive = 1
        
        # 오늘(또는 어제)부터 하루씩 빼가며 연속되는지 확인합니다.
        # 오늘 일기를 쓴 경우, 이미 1일로 시작했으므로 그 이전 날짜부터 확인합니다.
        if consecutive == 1:
            for i in range(1, len(sorted_dates)):
                if sorted_dates[i] == start_date - timedelta(days=i):
                    consecutive += 1
                else:
                    break
        else: # 오늘 일기를 안 쓴 경우
            for i, date in enumerate(sorted_dates):
                if date == start_date - timedelta(days=i):
                    consecutive += 1
                else:
                    break
                    
        return consecutive
    except Exception as e:
        print(f"연속 작성일 계산 오류: {e}")
        return 0

def generate_emotion_keywords(chat_messages, mood):
    """대화 내용을 바탕으로 AI가 감정 키워드 5개 제시"""
    try:
        ai_model = get_ai_model()
        
        if not chat_messages:
            # 기본 감정 키워드 (대화 내용이 없을 때)
            default_keywords = {
                "좋음": ["#기쁨", "#활기", "#만족", "#희망", "#평온"],
                "보통": ["#평범", "#일상", "#차분", "#보통", "#안정"],
                "나쁨": ["#우울", "#피곤", "#스트레스", "#불안", "#힘듦"]
            }
            return default_keywords.get(mood, ["#감정나눔", "#일상", "#생각", "#마음", "#기분"])
        
        # 대화 내용에서 사용자 메시지만 추출
        user_messages = []
        for msg in chat_messages:
            if isinstance(msg, dict) and msg.get("role") == "user":
                user_messages.append(msg.get("content", ""))
        
        conversation_text = "\n".join(user_messages)
        if len(conversation_text) > 1500:
            conversation_text = conversation_text[:1500] + "..."
        
        prompt = f"""다음 대화 내용을 분석해서 사용자의 감정을 나타내는 키워드 5개를 제시해주세요.

대화 내용:
{conversation_text}

현재 기분: {mood}

요청사항:
- 대화에서 느껴지는 구체적인 감정 키워드 5개
- 각 키워드는 # 붙여서 해시태그 형태로
- 사용자가 실제로 느꼈을 감정들 위주로
- 너무 추상적이지 않고 구체적으로

응답 형식:
#키워드1, #키워드2, #키워드3, #키워드4, #키워드5"""

        result = ai_model.generate_response(prompt)
        
        # 키워드 파싱
        keywords = [k.strip() for k in result.split(',') if k.strip().startswith('#')]
        
        # 5개가 안 나왔으면 기본값으로 채우기
        if len(keywords) < 5:
            default_extras = ["#감정나눔", "#일상", "#생각", "#마음", "#기분"]
            keywords.extend(default_extras[:5-len(keywords)])
        
        return keywords[:5]
        
    except Exception as e:
        print(f"감정 키워드 생성 오류: {e}")
        # 오류 시 기분별 기본 키워드
        default_keywords = {
            "좋음": ["#기쁨", "#활기", "#만족", "#희망", "#평온"],
            "보통": ["#평범", "#일상", "#차분", "#보통", "#안정"],
            "나쁨": ["#우울", "#피곤", "#스트레스", "#불안", "#힘듦"]
        }
        return default_keywords.get(mood, ["#감정나눔", "#일상", "#생각", "#마음", "#기분"])

def generate_emotion_stats():
    """감정 통계 생성 (선택된 키워드 기준)"""
    try:
        if not st.session_state.diary_entries:
            return None
        
        # 기분별 통계
        mood_counts = {}
        # 감정 키워드별 통계
        keyword_counts = {}
        
        for entry in st.session_state.diary_entries:
            try:
                # 기분 통계
                mood = entry.get('mood', '알 수 없음')
                mood_counts[mood] = mood_counts.get(mood, 0) + 1
                
                # 키워드 통계 (사용자가 선택한 것들)
                keywords = entry.get('keywords', [])
                for keyword in keywords:
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
                    
            except Exception:
                continue
        
        # 기분 통계
        total = sum(mood_counts.values())
        mood_stats = []
        for mood, count in mood_counts.items():
            percentage = (count / total) * 100
            mood_stats.append({
                'mood': mood,
                'count': count,
                'percentage': round(percentage, 1)
            })
        
        # 인기 키워드 통계 (상위 10개)
        popular_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'mood_stats': sorted(mood_stats, key=lambda x: x['count'], reverse=True),
            'popular_keywords': popular_keywords
        }
        
    except Exception:
        return None

def search_diaries(keyword):
    """일기 검색"""
    try:
        if not keyword or not st.session_state.diary_entries:
            return []
        
        results = []
        keyword_lower = keyword.lower()
        
        for entry in st.session_state.diary_entries:
            try:
                summary = entry.get('summary', '').lower()
                keywords = ' '.join(entry.get('keywords', [])).lower()
                
                if keyword_lower in summary or keyword_lower in keywords:
                    results.append(entry)
            except Exception:
                continue
        
        return results
    except Exception:
        return []

def export_diary_data():
    """일기 데이터 내보내기 (휴지통 포함)"""
    try:
        active_count = len(st.session_state.diary_entries)
        deleted_count = len(st.session_state.deleted_entries)
        
        if active_count == 0 and deleted_count == 0:
            return "내보낼 일기가 없어요."
        
        export_text = "=== 💜 마음톡 감정일기 백업 ===\n\n"
        
        # 활성 일기들
        if active_count > 0:
            export_text += f"📚 나의 일기들 ({active_count}개)\n"
            export_text += "=" * 50 + "\n\n"
            
            for i, entry in enumerate(st.session_state.diary_entries):
                try:
                    export_text += f"📅 날짜: {entry.get('date', '날짜 없음')} {entry.get('time', '')}\n"
                    export_text += f"😊 기분: {entry.get('mood', '기분 없음')}\n"
                    export_text += f"📝 오늘 있었던 일: {entry.get('summary', '내용 없음')}\n"
                    
                    if entry.get('keywords'):
                        export_text += f"🏷️ 감정 키워드: {', '.join(entry['keywords'])}\n"
                    
                    if entry.get('action_items'):
                        export_text += f"💡 AI 친구의 조언:\n"
                        for item in entry['action_items']:
                            export_text += f"   • {item}\n"
                    
                    export_text += "\n" + "-"*30 + "\n\n"
                except Exception:
                    continue
        
        # 휴지통 일기들
        if deleted_count > 0:
            export_text += f"\n🗑️ 임시 보관함 ({deleted_count}개)\n"
            export_text += "=" * 50 + "\n\n"
            
            for i, entry in enumerate(st.session_state.deleted_entries):
                try:
                    export_text += f"📅 원본 날짜: {entry.get('date', '날짜 없음')} {entry.get('time', '')}\n"
                    export_text += f"🗑️ 보관함에 들어온 날: {entry.get('deleted_date', '알 수 없음')}\n"
                    export_text += f"⏰ 자동삭제 예정일: {entry.get('auto_delete_date', '알 수 없음')}\n"
                    export_text += f"😊 기분: {entry.get('mood', '기분 없음')}\n"
                    export_text += f"📝 오늘 있었던 일: {entry.get('summary', '내용 없음')}\n"
                    
                    if entry.get('keywords'):
                        export_text += f"🏷️ 감정 키워드: {', '.join(entry['keywords'])}\n"
                    
                    export_text += "\n" + "-"*30 + "\n\n"
                except Exception:
                    continue
        
        export_text += f"\n📊 총계: 일기 {active_count}개, 임시보관 {deleted_count}개\n"
        export_text += f"백업 날짜: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}"
        
        return export_text
    except Exception as e:
        return f"❌ 데이터 내보내기 중 문제가 생겼어요: {str(e)}"

# ✅ 화면 함수들
def show_login():
    # 로그인 화면 제목 크기 조절 (font-size 수정)
    st.markdown("""
    <style>
    .login-card {
        background: linear-gradient(135deg, #faf9fc 0%, #f3e5f5 100%);
        border-radius: 24px;
        padding: 2.5rem 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(156, 39, 176, 0.2);
        max-width: 400px;
        width: 100%;
        border: 2px solid rgba(156, 39, 176, 0.1);
        margin: 2rem auto;
    }
    .login-title-heart {
        font-size: 2.5rem;
        color: #7b1fa2;
        margin-bottom: -0.5rem;
    }
    .login-title {
        font-size: 2.2rem;
        font-weight: bold;
        color: #7b1fa2;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .login-subtitle {
        font-size: 1.2rem;
        color: #8e24aa;
        margin-bottom: 1.5rem;
        opacity: 0.8;
    }
    .login-welcome {
        font-size: 1.1rem;
        color: #6a1b9a;
        margin-bottom: 1.5rem;
        font-weight: 500;
    }
    .stButton > button {
        background: linear-gradient(135deg, #e1bee7 0%, #f3e5f5 100%) !important;
        color: #7b1fa2 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: bold !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 15px rgba(156, 39, 176, 0.4) !important;
        transition: all 0.3s ease !important;
        height: auto !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #ce93d8 0%, #e1bee7 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(156, 39, 176, 0.6) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # 로그인 화면 HTML 구조 변경 (하트와 텍스트 분리)
        st.markdown("""
        <div class="login-card">
            <div class="login-title-heart">💜</div>
            <div class="login-title">마음톡</div>
            <div class="login-subtitle">나만의 감정일기</div>
            <div class="login-welcome">✨ 오늘의 감정을 함께 나눠봐요 ✨</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        
        if st.button("💜 마음톡 시작하기", use_container_width=True, key="login_button"):
            if password.strip() == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ 비밀번호가 맞지 않아요")

def show_mood_selection():
    # AI 이름 뒤에 붙는 조사(이/가)를 자연스럽게 처리
    ai_name = st.session_state.ai_name
    postposition = get_korean_postposition(ai_name)

    st.markdown(f"""
    <div style="text-align: center; padding: 1rem; margin-top: -1rem; margin-bottom: 2rem;">
        <div style="font-size: 2.5rem; font-weight: bold; color: #333; margin-bottom: 0.5rem;">
            오늘 기분 어떠세요?
        </div>
        <div style="font-size: 1.1rem; color: #666;">
            AI 친구 <b>{ai_name}</b>{postposition} 당신의 이야기를 기다리고 있어요 🌙
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Custom SVG buttons for mood selection
    st.markdown("""
    <style>
        .mood-container {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 1rem;
            margin-top: 2rem;
            margin-bottom: 2rem;
        }
        .mood-button {
            text-decoration: none;
            transition: transform 0.2s ease-in-out;
            filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.1));
        }
        .mood-button:hover {
            transform: scale(1.08) translateY(-5px);
            filter: drop-shadow(0px 8px 12px rgba(0,0,0,0.15));
        }
    </style>
    """, unsafe_allow_html=True)

    # SVG definitions
    good_svg = """
    <svg width="180" height="180" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <path d="M 8 15 C 8 8, 15 8, 22 8 L 78 8 C 85 8, 92 8, 92 15 L 92 85 C 92 92, 85 92, 78 92 L 22 92 C 15 92, 8 92, 8 85 Z" fill="#FFC107"/>
      <circle cx="35" cy="40" r="4" fill="black"/>
      <circle cx="65" cy="40" r="4" fill="black"/>
      <path d="M 35 60 Q 50 75, 65 60" stroke="black" stroke-width="4" fill="none" stroke-linecap="round"/>
      <text x="50" y="93" font-family="sans-serif" font-size="12" fill="#424242" text-anchor="middle" font-weight="bold">좋아!</text>
    </svg>
    """
    normal_svg = """
    <svg width="180" height="180" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="50" r="42" fill="#81D4FA"/>
      <circle cx="35" cy="40" r="4" fill="black"/>
      <circle cx="65" cy="40" r="4" fill="black"/>
      <line x1="35" y1="65" x2="65" y2="65" stroke="black" stroke-width="4" stroke-linecap="round"/>
      <text x="50" y="93" font-family="sans-serif" font-size="12" fill="#424242" text-anchor="middle" font-weight="bold">그냥 뭐..</text>
    </svg>
    """
    bad_svg = """
    <svg width="180" height="180" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <path d="M 17 29 C 5 45, 11 81, 27 89 C 43 97, 75 99, 87 81 C 99 63, 101 35, 87 21 C 73 7, 42 3, 27 11 C 12 19, 29 13, 17 29 Z" fill="#B39DDB"/>
      <circle cx="38" cy="42" r="4" fill="black"/>
      <circle cx="62" cy="42" r="4" fill="black"/>
      <path d="M 38 70 Q 50 55, 62 70" stroke="black" stroke-width="4" fill="none" stroke-linecap="round"/>
      <text x="50" y="93" font-family="sans-serif" font-size="12" fill="#424242" text-anchor="middle" font-weight="bold">별루야..</text>
    </svg>
    """

    # Using query params for clickable SVGs
    st.markdown(f"""
    <div class="mood-container">
        <a href="?mood=good" target="_self" class="mood-button">{good_svg}</a>
        <a href="?mood=normal" target="_self" class="mood-button">{normal_svg}</a>
        <a href="?mood=bad" target="_self" class="mood-button">{bad_svg}</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                color: #495057; 
                border-radius: 15px; 
                padding: 1.2rem; 
                text-align: center; 
                font-size: 1rem; 
                margin: 2rem auto 1rem auto;
                max-width: 600px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);">
        ☁️ 기분에 따라 {st.session_state.ai_name}{get_korean_postposition(st.session_state.ai_name)} 다르게 대화한답니다!
    </div>
    """, unsafe_allow_html=True)
    
    # 메뉴 추가 (4개로 간소화)
    st.markdown("---")
    st.markdown("### 📋 메뉴")
    
    menu_cols = st.columns(4)
    
    with menu_cols[0]:
        if st.button("📊\n\n감정 통계", key="menu_statistics_home", use_container_width=True):
            st.session_state.current_step = "statistics"
            st.rerun()
    
    with menu_cols[1]:
        if st.button("📅\n\n감정 달력", key="menu_calendar_home", use_container_width=True):
            st.session_state.current_step = "calendar"
            st.rerun()
    
    with menu_cols[2]:
        if st.button("🗑️\n\n휴지통", key="menu_trash_home", use_container_width=True):
            st.session_state.current_step = "trash"
            st.rerun()
    
    with menu_cols[3]:
        if st.button("⚙️\n\n설정", key="menu_settings_home", use_container_width=True):
            st.session_state.current_step = "settings"
            st.rerun()
    
    # 최근 일기들 (더 많이 표시)
    if st.session_state.diary_entries:
        st.markdown("---")
        st.markdown("### 📚 최근에 쓴 일기들")
        
        # 검색 기능 추가
        search_keyword = st.text_input("🔍 일기 검색", placeholder="찾고 싶은 키워드를 써봐요", key="home_search_diary")
        
        # 표시할 일기들 선택
        entries_to_show = st.session_state.diary_entries[-7:][::-1]  # 최근 7개, 최신순
        
        if search_keyword:
            search_results = search_diaries(search_keyword)
            entries_to_show = search_results[::-1] if search_results else []
            if search_results:
                st.success(f"🔍 '{search_keyword}' 검색 결과: {len(search_results)}개 발견!")
            else:
                st.info(f"🔍 '{search_keyword}'와 관련된 일기를 찾을 수 없어요.")
        
        for i, entry in enumerate(entries_to_show):
            mood_emoji = {"좋음": "😊", "보통": "😐", "나쁨": "😔"}.get(entry['mood'], "")
            
            # 일기 제목에 삭제 버튼 추가
            col1, col2 = st.columns([10, 1])
            
            with col1:
                expander_title = f"{mood_emoji} {entry['date']} {entry.get('time', '')} - {entry['mood']}"
            
            with col2:
                delete_key = f"home_delete_{entry['date']}_{entry.get('time', '')}_{i}_{hash(entry['summary'])}"
                if st.button("🗑️", key=delete_key, help="임시 보관함으로 이동"):
                    if move_to_trash(entry):
                        st.success("📦 일기가 임시 보관함으로 이동했어요!")
                        st.info("💡 30일 동안 보관하다가 자동으로 삭제될 거예요.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ 일기 삭제 중에 문제가 생겼어요.")
            
            # 일기 내용 표시
            with st.expander(expander_title):
                st.markdown(f"**📝 그날 있었던 일:** {entry.get('summary', '내용 없음')}")
                
                # 선택된 감정 키워드 표시
                if entry.get('keywords'):
                    st.markdown(f"**🏷️ 감정:** {', '.join(entry['keywords'])}")
                
                # AI가 제시했던 원본 키워드도 표시 (있다면)
                if entry.get('suggested_keywords'):
                    with st.expander("🤖 AI가 추천했던 감정들"):
                        st.write(' '.join(entry['suggested_keywords']))
                
                if entry.get('action_items'):
                    st.markdown("**💡 AI 친구의 조언:**")
                    for item in entry['action_items']:
                        st.markdown(f"• {item}")
        
        # 더 많은 일기가 있을 때 안내
        if len(st.session_state.diary_entries) > 7 and not search_keyword:
            st.info(f"📚 총 {len(st.session_state.diary_entries)}개의 일기가 있어요! 검색으로 더 찾아보세요.")

def show_chat():
    current_mood = st.session_state.get('current_mood', '선택하지 않음')
    mood_emoji = {"좋음": "😊", "보통": "😐", "나쁨": "😔"}.get(current_mood, "❓")
    
    st.markdown(f"""
    <div class="main-header">
        <h1>💬 {st.session_state.ai_name}와 대화하기</h1>
        <p style="font-size: 18px;">
            오늘 기분: {mood_emoji} {current_mood} | 편하게 이야기해봐요
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 기분이 선택되지 않았을 때 친근한 안내
    if not current_mood or current_mood == '선택하지 않음':
        st.markdown("""
        <div style='background: linear-gradient(45deg, #fff3e0, #ffe0b2); 
                    padding: 1.5rem; border-radius: 15px; text-align: center; margin: 1rem 0;'>
            <h3 style='color: #f57c00; margin-bottom: 1rem;'>🤔 어? 기분을 안 골랐네요!</h3>
            <p style='color: #ef6c00; font-size: 1.1rem;'>먼저 오늘 기분이 어떤지 알려주세요! 😊</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🎭 기분 선택하러 가기", use_container_width=True, key="select_mood_from_chat"):
            st.session_state.current_step = "mood_selection"
            st.rerun()
        return
    
    display_token_bar()

    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_messages:
            mood_messages = {
                "좋음": "오늘 기분이 좋았군요.",
                "보통": "오늘은 평범한 하루였군요.",
                "나쁨": "오늘 좀 힘드셨군요."
            }
            mood_message = mood_messages.get(st.session_state.current_mood, "오늘 하루 어땠어요?")
            
            st.markdown(f"""
            <div class="ai-message">
                <b>{st.session_state.ai_name}</b>: 안녕하세요! 저는 {st.session_state.ai_name}예요. 
                {mood_message}. 오늘 무슨 일이 있었는지 편하게 얘기해볼까요? 😊
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.chat_messages:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="user-message">
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="ai-message">
                        <b>{st.session_state.ai_name}</b>: {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")
    
    with st.form("chat_form_input", clear_on_submit=True):
        user_input = st.text_area(
            "💬 저에게 말해보세요.",
            height=80,
            placeholder="오늘 있었던 일, 지금 기분...편하게 말해보세요. 제가 잘 들어줄게요",
            help=f"무슨 이야기든 좋아요! {st.session_state.ai_name}가 잘 들어줄게요 🌙"
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            send_button = st.form_submit_button("📤 보내기", use_container_width=True)
        
        with col2:
            if st.form_submit_button("💾 일기로 저장하기", use_container_width=True):
                if st.session_state.chat_messages:
                    st.session_state.current_step = "summary"
                    st.rerun()
                else:
                    st.warning("아직 대화한 내용이 없어요!")
        
        with col3:
            if st.form_submit_button("🏠 처음으로", use_container_width=True):
                st.session_state.current_step = "mood_selection"
                st.session_state.chat_messages = []
                st.rerun()
        
        if send_button and user_input.strip():
            history_for_ai = st.session_state.chat_messages.copy()
            st.session_state.chat_messages.append({"role": "user", "content": user_input.strip()})

            with st.spinner(f"{st.session_state.ai_name}가 답장을 쓰고 있어요..."):
                # 유해 콘텐츠 검사
                danger_context = ""
                if check_harmful_content(user_input.strip()):
                    danger_context = "\n\n중요: 사용자가 자해나 자살 관련 내용을 언급했습니다. 공감적으로 반응한 후 자연스럽게 전문 상담 연락처를 안내해주세요."
                elif check_violence_content(user_input.strip()):
                    danger_context = "\n\n중요: 사용자가 폭력이나 위험 상황을 언급했습니다. 안전을 우선시하며 적절한 도움 연락처를 안내해주세요."
                
                ai_model = get_ai_model()
                ai_result = ai_model.get_ai_response(
                    user_input.strip() + danger_context,
                    history_for_ai,
                    st.session_state.conversation_context,
                    st.session_state.get('current_mood', '보통'),
                    st.session_state.ai_name
                )
            
            if ai_result["success"]:
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": ai_result["response"]
                })
                # 토큰 사용량 업데이트 (로컬 모델이므로 실제로는 무의미하지만 UI 유지)
                st.session_state.token_usage += ai_result.get("tokens_used", 0)
            else:
                st.session_state.chat_messages.pop() # Remove user message if AI fails
                st.error(f"❌ {ai_result['response']}")
            
            st.rerun()

def show_summary():
    if not st.session_state.chat_messages:
        st.error("대화한 내용이 없어요. 먼저 이야기하러 갈까요? 😊")
        if st.button("💬 대화하러 가기", key="go_to_chat_from_summary"):
            st.session_state.current_step = "mood_selection"
            st.rerun()
        return
    
    # AI 요약 생성
    if 'temp_summary' not in st.session_state:
        with st.spinner("✨ AI가 오늘 있었던 일을 정리하고 있어요..."):
            ai_model = get_ai_model()
            summary_result = ai_model.generate_conversation_summary(st.session_state.chat_messages)
            st.session_state.temp_summary = summary_result
    
    summary_data = st.session_state.temp_summary
    
    st.markdown(f"""
    <div class="summary-box">
        <h3>📝 오늘 있었던 일 요약</h3>
        <p style="font-size: 16px; line-height: 1.6;">{summary_data['summary']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # AI가 감정 키워드 5개 제시
    if 'suggested_emotions' not in st.session_state:
        with st.spinner("🎨 어떤 감정이 느껴지는지 분석하고 있어요..."):
            current_mood = st.session_state.get('current_mood', '보통')
            suggested_emotions = generate_emotion_keywords(st.session_state.chat_messages, current_mood)
            st.session_state.suggested_emotions = suggested_emotions
    
    st.markdown("### 🏷️ 감정 키워드")
    st.markdown("**AI가 대화 속에서 느껴졌던 감정들이랍니다. 마음에 드는 것들을 골라보세요.**")
    
    # 감정 키워드 선택
    selected_emotions = []
    emotion_cols = st.columns(5)
    
    for i, emotion in enumerate(st.session_state.suggested_emotions):
        with emotion_cols[i]:
            checkbox_key = f"emotion_select_{i}_{emotion}_{hash(emotion)}"
            if st.checkbox(emotion, key=checkbox_key):
                selected_emotions.append(emotion)
    
    # 직접 입력 옵션 (1개만 허용)
    st.markdown("**나만의 감정도 한 개만 써 볼까요?**")
    custom_emotion = st.text_input("💭 나만의 감정", 
                                 placeholder="예: 설렘, 행복함, 걱정",
                                   key="custom_emotion_input")
    
    if custom_emotion:
        # 여러 개 입력한 경우 첫 번째만 사용
        custom_emotions = [e.strip() for e in custom_emotion.split(',') if e.strip()]
        if len(custom_emotions) > 1:
            st.warning("🌈 한 번에 하나씩만 써주세요! 첫 번째 감정만 사용할게요.")
            custom_emotions = custom_emotions[:1]
        
        if custom_emotions:
            custom_emotion_formatted = custom_emotions[0] if custom_emotions[0].startswith('#') else f"#{custom_emotions[0]}"
            selected_emotions.append(custom_emotion_formatted)
    
    # 선택 검증 - 친근하게
    if len(selected_emotions) > 4:  # AI 추천 3개 + 사용자 입력 1개 = 최대 4개
        st.warning("🌈 감정이 너무 많아요! AI 추천 3개 + 내가 추가한 1개 = 총 4개까지만 가능해요!")
        selected_emotions = selected_emotions[:4]
    elif len(selected_emotions) == 0:
        st.info("💡 어떤 감정이 느껴지나요? 하나라도 선택해주세요!")
    
    # 선택된 감정 표시
    if selected_emotions:
        st.markdown("**선택한 감정들:**")
        emotion_text = " ".join(selected_emotions)
        st.markdown(f"<div style='padding: 1rem; background: linear-gradient(45deg, #f0f8ff, #e1f5fe); border-radius: 15px; color: #1565c0; font-weight: bold; text-align: center; font-size: 1.1rem;'>{emotion_text}</div>", 
                   unsafe_allow_html=True)
    
    # AI 제안사항
    if summary_data.get('action_items'):
        st.markdown("### 💡 AI 친구의 따뜻한 조언")
        for item in summary_data['action_items']:
            st.markdown(f"• {item}")
    
    # 저장 버튼
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        save_disabled = len(selected_emotions) == 0
        if st.button("💾 오늘의 마음 저장하기", use_container_width=True, disabled=save_disabled, 
                     help="감정을 선택해야 저장할 수 있어요!" if save_disabled else "오늘의 감정을 저장합니다.",
                     key="save_diary_button"):
            # 일기 데이터 생성
            today = datetime.now()
            diary_entry = {
                'date': today.strftime('%Y-%m-%d'),
                'time': today.strftime('%H:%M'),
                'mood': st.session_state.current_mood,
                'summary': summary_data['summary'],
                'keywords': selected_emotions,  # 사용자가 선택한 감정들
                'suggested_keywords': st.session_state.suggested_emotions,  # AI가 제시한 원본
                'action_items': summary_data.get('action_items', []),
                'chat_messages': st.session_state.chat_messages.copy()
            }
            
            # SQLite에 일기 저장
            if save_diary_to_db(diary_entry):
                # 세션에도 추가 (즉시 반영을 위해)
                st.session_state.diary_entries.append(diary_entry)
                
                st.session_state.conversation_context.append({
                    'summary': summary_data['summary'],
                    'action_items': summary_data.get('action_items', [])
                })
                
                st.session_state.consecutive_days = calculate_consecutive_days()
                st.session_state.last_entry_date = today.strftime('%Y-%m-%d')
                
                # 설정 정보 저장
                save_data_to_db()
                
                # 임시 데이터 정리
                for key in ['temp_summary', 'suggested_emotions']:
                    if key in st.session_state:
                        del st.session_state[key]
                
                st.success(f"✅ 오늘의 마음이 저장되었습니다! (감정: {', '.join(selected_emotions)})")
                st.balloons()
                st.session_state.current_step = "mood_selection"
                st.session_state.chat_messages = []
                st.rerun()
            else:
                st.error("❌ 일기 저장 중에 문제가 생겼어요.")
    with col2:
        if st.button("🏠 처음으로", use_container_width=True, key="home_from_summary"):
            st.session_state.current_step = "mood_selection"
            st.session_state.chat_messages = []
            for key in ['temp_summary', 'suggested_emotions']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

def show_trash():
    st.markdown("""
    <div class="main-header">
        <h1>🗑️ 휴지통</h1>
        <p>30일 동안 임시로 보관되는 일기들이에요</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 만료된 휴지통 항목 자동 정리
    clean_expired_trash()
    
    # 최신 데이터 강제 새로고침
    st.session_state.deleted_entries = load_deleted_entries_from_db()
    
    # 휴지통 내용
    deleted_entries = st.session_state.deleted_entries
    
    st.markdown(f"### 🗑️ 현재 {len(deleted_entries)}개의 일기가 임시 보관중이에요")
    
    if not deleted_entries:
        st.info("🗑️ 휴지통이 비어있어요.")
        st.markdown("💡 일기를 삭제하면 30일 동안 여기서 보관돼요.")
        
        # 홈으로 돌아가기 버튼
        if st.button("🏠 홈으로 돌아가기", use_container_width=True, key="home_from_empty_trash"):
            st.session_state.current_step = "mood_selection"
            st.rerun()
        return
    
    st.info("💡 여기 있는 일기들은 30일 후에 자동으로 완전히 삭제돼요.")
    
    # 전체 비우기 버튼
    if st.button("🗑️ 휴지통 전체 비우기", type="secondary", key="empty_all_trash"):
        if st.checkbox("정말로 휴지통을 완전히 비울거예요? (다시 돌릴 수 없어요)", key="confirm_empty_all_trash"):
            try:
                # SQLite에서 모든 휴지통 항목 삭제
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM deleted_entries')
                conn.commit()
                conn.close()
                
                # 세션에서도 업데이트
                st.session_state.deleted_entries = []
                st.success("🗑️ 휴지통이 완전히 비워졌어요.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 휴지통 비우기 중 오류: {e}")
    
    st.markdown("---")
    
    # 휴지통 일기들 표시
    for i, entry in enumerate(deleted_entries):
        mood_emoji = {"좋음": "😊", "보통": "😐", "나쁨": "😔"}.get(entry['mood'], "")
        deleted_date = entry.get('deleted_date', '알 수 없음')
        auto_delete_date = entry.get('auto_delete_date', '알 수 없음')
        
        with st.expander(f"🗑️ {mood_emoji} {entry['date']} - {entry['mood']} (삭제일: {deleted_date})"):
            st.markdown(f"**📝 그날 있었던 일:** {entry.get('summary', '내용 없음')}")
            if entry.get('keywords'):
                st.markdown(f"**🏷️ 감정:** {' '.join(entry['keywords'])}")
            st.markdown(f"**⏰ 자동 삭제 예정일:** {auto_delete_date}")
            
            col1, col2 = st.columns(2)
            with col1:
                restore_key = f"restore_trash_{i}_{entry['date']}_{entry.get('time', '')}_{hash(entry['summary'])}"
                if st.button("↩️ 다시 가져오기", key=restore_key, use_container_width=True):
                    if restore_from_trash(entry):
                        st.success("✅ 일기가 다시 돌아왔어!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ 복원 중에 문제가 생겼어요.")
            with col2:
                permanent_delete_key = f"permanent_trash_{i}_{entry['date']}_{entry.get('time', '')}_{hash(entry['summary'])}"
                if st.button("🔥 완전히 삭제", key=permanent_delete_key, use_container_width=True, type="secondary"):
                    confirm_key = f"confirm_permanent_trash_{i}_{entry['date']}_{hash(entry['summary'])}"
                    if st.checkbox("정말로 완전히 삭제할거예요? (다시 돌릴 수 없어요)", key=confirm_key):
                        if permanent_delete_from_trash(entry):
                            st.success("🔥 일기가 완전히 삭제되었어요.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ 완전 삭제 중에 문제가 생겼어요.")
    
    # 홈으로 버튼
    st.markdown("---")
    if st.button("🏠 홈으로", key="home_from_trash"):
        st.session_state.current_step = "mood_selection"
        st.rerun()

def show_calendar():
    st.markdown("""
    <div class="main-header">
        <h1>📅 감정 달력</h1>
        <p>달마다 내 감정 패턴을 확인해봐요</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.diary_entries:
        st.info("📝 아직 쓴 일기가 없어요.")
        if st.button("✍️ 일기 써보기", key="write_diary_from_calendar"):
            st.session_state.current_step = "mood_selection"
            st.rerun()
        return
    
    # 월 선택
    today = datetime.now()
    selected_year = st.selectbox("연도", [today.year - 1, today.year, today.year + 1], index=1, key="calendar_year")
    selected_month = st.selectbox("월", list(range(1, 13)), index=today.month - 1, key="calendar_month")
    
    # 해당 월의 일기 데이터 (하루에 여러 개일 수 있으므로 list로 관리)
    month_entries = {}
    for entry in st.session_state.diary_entries:
        try:
            entry_date = datetime.strptime(entry['date'], '%Y-%m-%d')
            if entry_date.year == selected_year and entry_date.month == selected_month:
                day = entry_date.day
                if day not in month_entries:
                    month_entries[day] = []
                month_entries[day].append(entry)
        except:
            continue
    
    # 캘린더 표시
    st.markdown(f"### {selected_year}년 {selected_month}월")
    
    # 달력 그리기 - Streamlit 컬럼 방식으로 변경
    cal_obj = cal.monthcalendar(selected_year, selected_month)
    
    # 요일 헤더
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    header_cols = st.columns(7)
    
    for i, day_name in enumerate(weekdays):
        with header_cols[i]:
            st.markdown(f"<div style='text-align: center; font-weight: bold; padding: 10px; background: #f8f9fa; border-radius: 5px;'>{day_name}</div>", unsafe_allow_html=True)
    
    # 달력 본체 - 주 단위로 행 생성
    for week in cal_obj:
        week_cols = st.columns(7)
        
        for i, day in enumerate(week):
            with week_cols[i]:
                if day == 0:
                    # 빈 날짜
                    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
                else:
                    # 날짜 표시
                    mood_emoji = ""
                    bg_color = "#f8f9fa"
                    border_color = "#ddd"
                    tooltip_text = "이날은 일기를 쓰지 않았어요."
                    
                    if day in month_entries:
                        # 하루의 첫 번째 일기를 기준으로 대표 기분 설정
                        first_entry = month_entries[day][0]
                        mood = first_entry['mood']
                        mood_emoji = {"좋음": "😊", "보통": "😐", "나쁨": "😔"}.get(mood, "")
                        bg_colors = {"좋음": "#ffe4e6", "보통": "#e3f2fd", "나쁨": "#f3e5f5"}
                        border_colors = {"좋음": "#ffb3ba", "보통": "#90caf9", "나쁨": "#ce93d8"}
                        bg_color = bg_colors.get(mood, "#f8f9fa")
                        border_color = border_colors.get(mood, "#ddd")
                        
                        # 툴팁에 표시할 모든 키워드 수집
                        all_keywords = []
                        for entry in month_entries[day]:
                            all_keywords.extend(entry.get('keywords', []))
                        
                        if all_keywords:
                            tooltip_text = ", ".join(set(all_keywords))
                        else:
                            tooltip_text = "선택한 감정 키워드가 없어요."

                    # 오늘 날짜 표시
                    today_mark = ""
                    if (day == today.day and selected_month == today.month and selected_year == today.year):
                        today_mark = " 🔵"
                    
                    st.markdown(f"""
                    <div title='{tooltip_text}' style='
                        background: {bg_color}; 
                        padding: 15px; 
                        text-align: center; 
                        border-radius: 8px; 
                        border: 2px solid {border_color};
                        height: 80px;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        cursor: help;
                    '>
                        <div style='font-weight: bold; font-size: 16px;'>{day}{today_mark}</div>
                        <div style='font-size: 24px; margin-top: 5px;'>{mood_emoji}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # 감정 예시
    st.markdown("---")
    st.markdown("### 📖 설명")
    
    legend_cols = st.columns(4)
    
    with legend_cols[0]:
        st.markdown("""
        <div style='display: flex; align-items: center; padding: 10px; background: #ffe4e6; border-radius: 8px; margin: 5px 0;'>
            <span style='font-size: 20px; margin-right: 10px;'>😊</span>
            <span>좋은 기분</span>
        </div>
        """, unsafe_allow_html=True)
    
    with legend_cols[1]:
        st.markdown("""
        <div style='display: flex; align-items: center; padding: 10px; background: #e3f2fd; border-radius: 8px; margin: 5px 0;'>
            <span style='font-size: 20px; margin-right: 10px;'>😐</span>
            <span>보통 기분</span>
        </div>
        """, unsafe_allow_html=True)
    
    with legend_cols[2]:
        st.markdown("""
        <div style='display: flex; align-items: center; padding: 10px; background: #f3e5f5; border-radius: 8px; margin: 5px 0;'>
            <span style='font-size: 20px; margin-right: 10px;'>😔</span>
            <span>안 좋은 기분</span>
        </div>
        """, unsafe_allow_html=True)
    
    with legend_cols[3]:
        st.markdown("""
        <div style='display: flex; align-items: center; padding: 10px; background: #e8f4fd; border-radius: 8px; margin: 5px 0;'>
            <span style='font-size: 20px; margin-right: 10px;'>🔵</span>
            <span>오늘</span>
        </div>
        """, unsafe_allow_html=True)
    
    # 해당 월 통계
    if month_entries:
        st.markdown("---")
        st.markdown(f"### 📊 {selected_month}월 감정 요약")
        
        month_moods = []
        for day_entries in month_entries.values():
            # 하루에 여러 일기가 있어도 첫 번째 일기의 기분으로 통계 계산
            month_moods.append(day_entries[0]['mood'])

        mood_counts = {}
        for mood in month_moods:
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
        
        stats_cols = st.columns(len(mood_counts) if mood_counts else 1)
        
        if mood_counts:
            for i, (mood, count) in enumerate(mood_counts.items()):
                with stats_cols[i]:
                    mood_emoji = {"좋음": "😊", "보통": "😐", "나쁨": "😔"}.get(mood, "")
                    st.metric(f"{mood_emoji} {mood}", f"{count}일")
        else:
            stats_cols[0].info("이번 달에 기록된 기분이 없어요.")

    if st.button("🏠 홈으로", key="home_from_calendar"):
        st.session_state.current_step = "mood_selection"
        st.rerun()

def show_statistics():
    st.markdown("""
    <div class="main-header">
        <h1>📊 내 감정 통계</h1>
        <p>내 감정 패턴을 한눈에 확인해봐요</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.diary_entries:
        st.info("📝 아직 쓴 일기가 없어요. 첫 번째 일기를 써보아요!")
        if st.button("✍️ 일기 써보기", key="write_diary_from_statistics"):
            st.session_state.current_step = "mood_selection"
            st.rerun()
        return
    
    # 기본 통계
    total_entries = len(st.session_state.diary_entries)
    consecutive_days = calculate_consecutive_days()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("총 일기 수", f"{total_entries}개")
    
    with col2:
        st.metric("연속 작성일", f"{consecutive_days}일")
    
    with col3:
        if st.session_state.diary_entries:
            first_date_str = st.session_state.diary_entries[0]['date']
            first_date = datetime.strptime(first_date_str, '%Y-%m-%d').date()
            days_since_start = (datetime.now().date() - first_date).days + 1
            st.metric("일기 시작한 지", f"{days_since_start}일")
    
    # 감정 분포
    st.markdown("### 😊 내 감정 분포")
    emotion_stats = generate_emotion_stats()
    
    if emotion_stats and emotion_stats.get('mood_stats'):
        for stat in emotion_stats['mood_stats']:
            mood_emoji = {"좋음": "😊", "보통": "😐", "나쁨": "😔"}.get(stat['mood'], "")
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"{mood_emoji} {stat['mood']}")
            with col2:
                st.write(f"{stat['count']}번")
            with col3:
                st.write(f"{stat['percentage']}%")
            
            # 진행률 바
            st.progress(stat['percentage'] / 100)
    
    # 인기 키워드
    if emotion_stats and emotion_stats.get('popular_keywords'):
        st.markdown("### 🏷️ 자주 쓴 감정 키워드")
        for keyword, count in emotion_stats['popular_keywords']:
            st.markdown(f"**{keyword}**: {count}번")
    
    if st.button("🏠 홈으로", key="home_from_statistics"):
        st.session_state.current_step = "mood_selection"
        st.rerun()

def show_settings():
    st.markdown("""
    <div class="main-header">
        <h1>⚙️ 설정</h1>
        <p>마음톡을 내 스타일로 꾸며봐요</p>
    </div>
    """, unsafe_allow_html=True)
    
    # AI 이름 설정
    st.markdown("### 🤖 AI 친구 이름 바꾸기")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        new_ai_name = st.selectbox(
            "AI 친구 이름을 골라봐요",
            RECOMMENDED_AI_NAMES,
            index=RECOMMENDED_AI_NAMES.index(st.session_state.ai_name) if st.session_state.ai_name in RECOMMENDED_AI_NAMES else 0,
            key="ai_name_selector"
        )
    
    with col2:
        if st.button("이름 바꾸기", key="change_ai_name"):
            st.session_state.ai_name = new_ai_name
            save_data_to_db()
            st.success(f"AI 친구 이름이 '{new_ai_name}'로 바뀌었어요!")
            st.rerun()
    
    # 테마 설정
    st.markdown("### 🎨 테마 바꾸기")
    
    theme_cols = st.columns(4)
    
    for i, (theme_name, theme_data) in enumerate(THEMES.items()):
        with theme_cols[i]:
            theme_key = f"theme_select_{theme_name}_{i}"
            if st.button(f"{theme_name}", use_container_width=True, key=theme_key):
                st.session_state.selected_theme = theme_name
                save_data_to_db()
                st.success(f"{theme_name} 테마가 적용되었어요!")
                st.rerun()
    
    # 데이터 관리
    st.markdown("### 💾 내 데이터 관리")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 일기 백업하기", key="backup_diary_data"):
            export_data = export_diary_data()
            st.download_button(
                label="💾 파일로 다운로드",
                data=export_data,
                file_name=f"마음톡_일기백업_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                key="download_backup"
            )
    
    with col2:
        if st.button("🗑️ 모든 일기 삭제", key="delete_all_diaries"):
            if st.session_state.diary_entries:
                confirm_key = "confirm_delete_all_diaries"
                if st.checkbox("정말로 모든 일기를 삭제할거예요? (임시 보관함으로 이동)", key=confirm_key):
                    # 모든 일기를 휴지통으로 이동
                    moved_count = 0
                    entries_to_move = st.session_state.diary_entries.copy()
                    
                    for entry in entries_to_move:
                        if move_to_trash(entry):
                            moved_count += 1
                    
                    if moved_count > 0:
                        st.success(f"📦 {moved_count}개의 일기가 임시 보관함으로 이동했어요.")
                        st.info("💡 임시 보관함에서 다시 가져오거나 30일 후에 자동 삭제돼요.")
                    else:
                        st.error("❌ 일기 삭제 중에 문제가 생겼어요.")
                    
                    st.session_state.conversation_context = []
                    st.rerun()
            else:
                st.info("삭제할 일기가 없어요.")
    
    # 휴지통 관리
    st.markdown("### 🗑️ 임시 보관함 관리")
    
    trash_count = len(st.session_state.deleted_entries)
    
    if trash_count > 0:
        st.info(f"🗑️ 임시 보관함에 {trash_count}개의 일기가 있어요.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📦 보관함 보기", key="view_trash_from_settings"):
                st.session_state.current_step = "trash"
                st.rerun()
        
        with col2:
            if st.button("🔥 보관함 완전히 비우기", key="empty_trash_from_settings"):
                confirm_key = "confirm_empty_trash_from_settings"
                if st.checkbox("보관함의 모든 일기를 완전히 삭제할거예요? (다시 돌릴 수 없어요)", key=confirm_key):
                    try:
                        # SQLite에서 모든 휴지통 항목 삭제
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM deleted_entries')
                        conn.commit()
                        conn.close()
                        
                        # 세션에서도 업데이트
                        st.session_state.deleted_entries = []
                        st.success("🔥 보관함이 완전히 비워졌어요.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 보관함 비우기 중 오류: {e}")
    else:
        st.info("🗑️ 임시 보관함이 비어있어요.")
    
    # 통계 정보
    if st.session_state.diary_entries or st.session_state.deleted_entries:
        st.markdown("### 📊 앱 사용 현황")
        
        total_entries = len(st.session_state.diary_entries)
        deleted_entries = len(st.session_state.deleted_entries)
        consecutive_days = calculate_consecutive_days()
        token_usage = st.session_state.get('token_usage', 0)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("내 일기", f"{total_entries}개")
        with col2:
            st.metric("임시 보관함", f"{deleted_entries}개")
        with col3:
            st.metric("연속 작성일", f"{consecutive_days}일")
        with col4:
            st.metric("AI 사용량", "무제한")
    
    if st.button("🏠 홈으로", key="home_from_settings"):
        st.session_state.current_step = "mood_selection"
        st.rerun()

# 하단 면책조항 함수
def show_footer():
    """브라우저 하단에 면책조항 표시"""
    st.markdown("""
    <div class="footer">
        ⚠️ <strong>알림:</strong> 
        이 앱은 감정 표현을 도와주는 도구일 뿐 전문적인 심리상담을 대신할 수는 없어요. 
        심각한 심리적 문제가 있다면 전문가와 상담하는 게 좋아요. |
        <strong>도움이 필요할 때:</strong> 
        자살예방상담 <strong>109</strong> | 청소년상담 <strong>1388</strong> |
        정신건강위기상담 <strong>1577-0199</strong>
    </div>
    """, unsafe_allow_html=True)

# ✅ 메인 함수
def main():
    if 'app_initialized' not in st.session_state:
        init_session_state()

    # SVG 버튼 클릭으로 URL에 'mood' 파라미터가 추가된 경우를 먼저 처리합니다.
    query_params = st.query_params
    if "mood" in query_params:
        mood_map = {"good": "좋음", "normal": "보통", "bad": "나쁨"}
        mood_value = query_params.get("mood")
        if mood_value in mood_map:
            # 인증 상태를 True로 설정하고, 선택된 기분으로 채팅 단계를 시작합니다.
            st.session_state.authenticated = True
            st.session_state.current_mood = mood_map[mood_value]
            st.session_state.current_step = "chat"
            st.session_state.chat_messages = []
            
            # 풍선 효과를 보여줍니다.
            st.balloons()
            
            # URL에서 파라미터를 제거합니다.
            st.query_params.clear()

            # 풍선 애니메이션이 보일 수 있도록 아주 짧은 딜레이를 줍니다.
            time.sleep(0.5)
            
            # 스크립트를 재실행하여 채팅 화면으로 넘어갑니다.
            st.rerun()

    # 테마 스타일을 적용합니다.
    st.markdown(get_theme_style(st.session_state.selected_theme), unsafe_allow_html=True)

    # 일반적인 경우의 인증 상태를 확인합니다.
    if not st.session_state.get("authenticated", False):
        show_login()
        return

    # 라우팅: 현재 단계에 맞는 화면을 보여줍니다.
    if st.session_state.current_step == "mood_selection":
        show_mood_selection()
    elif st.session_state.current_step == "chat":
        show_chat()
    elif st.session_state.current_step == "summary":
        show_summary()
    elif st.session_state.current_step == "trash":
        show_trash()
    elif st.session_state.current_step == "statistics":
        show_statistics()
    elif st.session_state.current_step == "calendar":
        show_calendar()
    elif st.session_state.current_step == "settings":
        show_settings()
    else:
        show_mood_selection()

    # 모든 페이지에서 하단 면책조항 표시
    show_footer()

if __name__ == "__main__":
    main()