import streamlit as st
from typing import List, Dict, Optional
import random
import time

class AIModelManager:
    """더미 AI 모델 (테스트용)"""
    
    def __init__(self):
        self.model_name = "dummy-model"
        print("✅ 더미 AI 모델 로딩 완료! (테스트용)")
    
    def _load_model(self):
        """더미 로드 함수"""
        pass
    
    def generate_response(self, prompt: str, max_new_tokens: int = 200, temperature: float = 0.7) -> str:
        """더미 텍스트 생성"""
        time.sleep(1)  # 실제 AI처럼 약간의 지연
        
        # 더미 응답들
        responses = [
            "그렇게 느끼셨군요. 어떤 부분이 가장 기억에 남나요?",
            "정말 힘드셨겠어요. 지금 기분이 어떠세요?",
            "와, 정말 좋은 일이네요! 더 자세히 말해주실래요?",
            "그런 상황이었군요. 어떻게 해결하려고 생각하고 계시나요?",
            "많이 고민되셨을 것 같아요. 누군가와 이야기하고 싶었겠어요."
        ]
        
        return random.choice(responses)
    
    def get_ai_response(self, user_message: str, conversation_history: List[Dict], 
                       context: List[Dict] = None, current_mood: str = "보통", 
                       ai_name: str = "루나") -> Dict:
        """더미 AI 응답 생성"""
        
        if not user_message or not user_message.strip():
            return {
                "response": "메시지를 입력해주세요.",
                "tokens_used": 0,
                "success": False
            }
        
        try:
            # 기분별 응답
            mood_responses = {
                "좋음": [
                    "기분이 좋으시니까 저도 기뻐요! 어떤 좋은 일이 있었나요?",
                    "정말 좋네요! 그 기분을 더 오래 느끼셨으면 좋겠어요.",
                    "와! 기분 좋은 이야기 더 들려주세요!"
                ],
                "보통": [
                    "평범한 하루였군요. 그래도 괜찮으세요?",
                    "보통인 날도 의미가 있어요. 어떤 하루였는지 말해주세요.",
                    "그런 날들이 있죠. 지금 기분은 어떠세요?"
                ],
                "나쁨": [
                    "힘든 하루였군요. 많이 속상하셨을 것 같아요.",
                    "그런 기분이 드시는군요. 혼자 견디기 힘드셨죠?",
                    "정말 고생 많으셨어요. 지금은 좀 어떠세요?"
                ]
            }
            
            responses = mood_responses.get(current_mood, mood_responses["보통"])
            ai_response = random.choice(responses)
            
            # 더미 지연
            time.sleep(1)
            
            return {
                "response": ai_response,
                "tokens_used": 50,  # 더미 토큰 수
                "success": True
            }
            
        except Exception as e:
            return {
                "response": "죄송해요. 일시적으로 문제가 생겼어요.",
                "tokens_used": 0,
                "success": False
            }
    
    def generate_conversation_summary(self, messages: List[Dict]) -> Dict:
        """더미 대화 요약 생성"""
        try:
            if not messages:
                return {
                    "summary": "대화 내용이 없어요",
                    "keywords": ["#감정나눔"],
                    "action_items": ["오늘도 고생 많았어요"],
                    "success": False
                }
            
            # 더미 요약
            dummy_summaries = [
                "오늘 하루 일상을 나누었어요",
                "친구와의 갈등에 대해 이야기했어요", 
                "학교/직장에서 있었던 일을 나누었어요",
                "가족과의 시간에 대해 얘기했어요"
            ]
            
            dummy_keywords = [
                ["#피곤", "#스트레스", "#힘듦", "#고민", "#불안"],
                ["#기쁨", "#만족", "#행복", "#설렘", "#평온"],
                ["#평범", "#일상", "#차분", "#보통", "#안정"]
            ]
            
            dummy_actions = [
                ["충분히 쉬어보세요", "좋아하는 것을 해보는 것은 어때요?", "오늘도 수고했어요"],
                ["그 기분을 더 오래 간직해보세요", "좋은 에너지를 계속 유지해봐요", "정말 멋져요!"],
                ["작은 변화를 만들어봐요", "자신을 더 사랑해주세요", "내일은 더 좋은 하루가 될 거예요"]
            ]
            
            # 더미 지연
            time.sleep(2)
            
            return {
                "summary": random.choice(dummy_summaries),
                "keywords": random.choice(dummy_keywords),
                "action_items": random.choice(dummy_actions),
                "success": True
            }
            
        except Exception:
            return {
                "summary": "요약을 만드는 중에 문제가 생겼어요",
                "keywords": ["#감정나눔"],
                "action_items": ["오늘도 고생 많았어요"],
                "success": False
            }

# 유틸리티 함수들
def check_harmful_content(text: str) -> bool:
    """유해 콘텐츠 검사"""
    if not text or not isinstance(text, str):
        return False
    
    harmful_patterns = [
        "자살", "죽고싶", "자해", "죽고싶어", "사라지고싶", "끝내고싶", 
        "살기싫", "살고싶지", "죽어버리", "죽었으면", "베고싶", "자살하고"
    ]
    
    text_lower = text.lower().replace(" ", "")
    return any(pattern in text_lower for pattern in harmful_patterns)

def check_violence_content(text: str) -> bool:
    """폭력 콘텐츠 검사"""
    if not text or not isinstance(text, str):
        return False
    
    violence_patterns = [
        "때리고싶", "죽이고싶", "칼", "총", "성폭행", "강간", "폭행", 
        "때렸다", "맞았다", "협박", "폭력", "성추행"
    ]
    
    text_lower = text.lower().replace(" ", "")
    return any(pattern in text_lower for pattern in violence_patterns)