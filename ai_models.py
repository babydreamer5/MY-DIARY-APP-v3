import streamlit as st
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from typing import List, Dict, Optional
import re

class AIModelManager:
    """허깅페이스 skt/A.X-4.0-Light 모델 관리 클래스"""
    
    def __init__(self):
        self.model_name = "skt/A.X-4.0-Light"
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.max_length = 2048
        self._load_model()
    
    def _load_model(self):
        """모델과 토크나이저 로드"""
        try:
            print(f"🤖 AI 모델 로딩 중... ({self.device})")
            
            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # 모델 로드
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True
            )
            
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            
            # 패딩 토큰 설정
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            print("✅ AI 모델 로딩 완료!")
            
        except Exception as e:
            print(f"❌ AI 모델 로딩 실패: {e}")
            st.error(f"AI 모델을 불러오는데 실패했습니다: {e}")
            st.info("💡 인터넷 연결을 확인하거나, 나중에 다시 시도해주세요.")
            raise e
    
    def generate_response(self, prompt: str, max_new_tokens: int = 200, temperature: float = 0.7) -> str:
        """텍스트 생성"""
        try:
            if not self.model or not self.tokenizer:
                return "AI 모델이 로드되지 않았습니다."
            
            # 입력 토큰화
            inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=self.max_length-max_new_tokens, truncation=True)
            inputs = inputs.to(self.device)
            
            # 생성 설정
            generation_config = {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "do_sample": True,
                "top_p": 0.9,
                "pad_token_id": self.tokenizer.eos_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
                "repetition_penalty": 1.1
            }
            
            # 텍스트 생성
            with torch.no_grad():
                outputs = self.model.generate(inputs, **generation_config)
            
            # 디코딩 (입력 부분 제외)
            generated_text = self.tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
            
            # 후처리
            generated_text = self._post_process_response(generated_text)
            
            return generated_text
            
        except Exception as e:
            print(f"텍스트 생성 오류: {e}")
            return "죄송해요. 답변을 생성하는 중에 문제가 생겼어요."
    
    def _post_process_response(self, text: str) -> str:
        """응답 후처리"""
        try:
            # 불필요한 공백 제거
            text = text.strip()
            
            # 중복 문장 제거
            sentences = text.split('.')
            unique_sentences = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and sentence not in unique_sentences:
                    unique_sentences.append(sentence)
            
            if unique_sentences:
                text = '. '.join(unique_sentences)
                if not text.endswith('.') and not text.endswith('!') and not text.endswith('?'):
                    text += '.'
            
            # 최대 길이 제한 (3문장 이내)
            sentences = text.split('.')
            if len(sentences) > 3:
                text = '. '.join(sentences[:3]) + '.'
            
            return text
            
        except Exception:
            return text
    
    def get_ai_response(self, user_message: str, conversation_history: List[Dict], 
                       context: List[Dict] = None, current_mood: str = "보통", 
                       ai_name: str = "루나") -> Dict:
        """AI 응답 생성 with 개선된 프롬프트"""
        
        if not user_message or not user_message.strip():
            return {
                "response": "메시지를 입력해주세요.",
                "tokens_used": 0,
                "success": False
            }
        
        try:
            # 컨텍스트 처리
            context_text = ""
            if context and isinstance(context, list):
                try:
                    recent_context = context[-2:]
                    context_summaries = []
                    for ctx in recent_context:
                        if isinstance(ctx, dict) and 'summary' in ctx and 'action_items' in ctx:
                            action_items = ctx.get('action_items', [])
                            if isinstance(action_items, list):
                                context_summaries.append(f"지난번에 이야기했던 것: {ctx['summary']}")
                    
                    if context_summaries:
                        context_text = "\n\n이전 대화 참고:\n" + "\n".join(context_summaries) + "\n\n"
                except Exception:
                    context_text = ""
            
            # 기분별 설정
            mood_styles = {
                "좋음": {
                    "tone": "밝고 활기찬 말투로 기쁨을 함께 나누세요",
                    "approach": "긍정적인 감정을 더 깊이 느낄 수 있도록 격려하세요",
                },
                "보통": {
                    "tone": "편안하고 자연스러운 말투로 대화하세요",
                    "approach": "일상의 소소한 의미를 찾을 수 있도록 도와주세요",
                },
                "나쁨": {
                    "tone": "부드럽고 따뜻한 말투로 위로하세요",
                    "approach": "힘든 감정을 안전하게 표현할 수 있도록 공간을 만들어주세요",
                }
            }
            
            mood_config = mood_styles.get(current_mood, mood_styles["보통"])
            
            # 대화 히스토리 준비
            conversation_text = ""
            if conversation_history and isinstance(conversation_history, list):
                for msg in conversation_history[-5:]:  # 최근 5개만
                    if isinstance(msg, dict):
                        role = msg.get("role", "")
                        content = msg.get("content", "")
                        if role == "user":
                            conversation_text += f"사용자: {content}\n"
                        elif role == "assistant":
                            conversation_text += f"{ai_name}: {content}\n"
            
            # 프롬프트 구성
            system_prompt = f"""당신은 10대를 위한 따뜻하고 공감적인 AI 친구 {ai_name}입니다.

핵심 원칙:
- 친구처럼 편하게 대화하되, 존댓말을 사용하세요
- 판단하지 말고 있는 그대로 공감해주세요
- 자해나 위험한 행동은 절대 권하지 마세요
- 응답은 2-3문장으로 간결하게 해주세요

현재 기분: {current_mood}
대화 스타일:
- {mood_config['tone']}
- {mood_config['approach']}
- 먼저 짧게 공감하고, 구체적인 질문 1개만 하세요

구체적 대화 가이드:
- 사용자가 구체적인 내용을 언급하면 그것에 대해 구체적으로 반응하세요
- 예: "수학시험 망했어" → "수학시험 어려웠구나. 어떤 부분이 가장 힘들었어요?"
- 예: "친구랑 싸웠어" → "친구와 싸우니 속상하겠어요. 어떤 일이 있었나요?"
- 일반적인 응답 대신 사용자의 상황에 맞춘 질문을 하세요

응답 길이: 최대 2-3문장으로 간결하게
응원 멘트: 과도한 응원보다는 자연스러운 공감 우선

위험 상황 대응:
- 자해/자살 언급 시: 공감 후 "이런 마음이 들 때는 전문가와 이야기하는 것이 도움될 수 있어요. 자살예방상담 109번이나 청소년상담 1388번에서 도움받을 수 있어요."
- 폭력 상황 언급 시: "안전이 가장 중요해요. 위험하다면 112번이나 청소년상담 1388번에 도움을 요청하세요."

{context_text}

간결하고 자연스러운 대화를 해주세요."""

            # 전체 프롬프트
            full_prompt = f"""{system_prompt}

{conversation_text}사용자: {user_message}
{ai_name}:"""

            # AI 응답 생성
            ai_response = self.generate_response(full_prompt, max_new_tokens=150, temperature=0.7)
            
            # 토큰 수 추정 (대략적)
            tokens_used = len(full_prompt.split()) + len(ai_response.split())
            
            return {
                "response": ai_response,
                "tokens_used": tokens_used,
                "success": True
            }
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "memory" in error_msg or "cuda" in error_msg:
                error_response = "메모리 부족으로 응답을 생성할 수 없어요. 잠시 후 다시 시도해주세요."
            elif "connection" in error_msg or "network" in error_msg:
                error_response = "네트워크 문제가 생겼어요. 인터넷 연결을 확인해주세요."
            else:
                error_response = "일시적으로 문제가 생겼어요. 다시 시도해주세요."
            
            return {
                "response": error_response,
                "tokens_used": 0,
                "success": False
            }
    
    def generate_conversation_summary(self, messages: List[Dict]) -> Dict:
        """대화 요약 생성"""
        try:
            if not messages or not isinstance(messages, list):
                return {
                    "summary": "대화 내용이 없어요",
                    "keywords": ["#감정나눔"],
                    "action_items": ["오늘도 고생 많았어요"],
                    "success": False
                }
            
            user_messages = []
            for msg in messages:
                try:
                    if isinstance(msg, dict) and msg.get("role") == "user" and msg.get("content"):
                        user_messages.append(msg["content"])
                except Exception:
                    continue
            
            if not user_messages:
                return {
                    "summary": "사용자 메시지가 없어요",
                    "keywords": ["#감정나눔"],
                    "action_items": ["오늘도 고생 많았어요"],
                    "success": False
                }
            
            conversation_text = "\n".join(user_messages)
            
            if len(conversation_text) > 1500:
                conversation_text = conversation_text[:1500] + "..."
            
            prompt = f"""다음 대화 내용을 분석해서 아래 형식으로 응답해주세요:

대화 내용:
{conversation_text}

분석 요청:
1. 오늘 있었던 일을 1-2줄로 요약
2. 대화에서 느껴진 감정 키워드 5개 추출 (예: #기쁨, #불안, #성취감 등)
3. 사용자에게 도움이 될 따뜻하고 친근한 조언 3개 제안 (친구 같은 말투로, ~해요/~랍니다 교차 사용)

응답 형식:
요약: [1-2줄 요약]
감정키워드: #키워드1, #키워드2, #키워드3, #키워드4, #키워드5
액션아이템: 
- [~해요 말투의 따뜻한 조언]
- [~랍니다 말투의 친근한 조언]
- [~해요 말투의 격려 메시지]"""

            result = self.generate_response(prompt, max_new_tokens=300, temperature=0.3)
            
            # 응답 파싱
            lines = result.strip().split('\n')
            summary = ""
            keywords = []
            action_items = []
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('요약:'):
                    summary = line.replace('요약:', '').strip()
                elif line.startswith('감정키워드:'):
                    keyword_text = line.replace('감정키워드:', '').strip()
                    keywords = [k.strip() for k in keyword_text.split(',') if k.strip()]
                elif line.startswith('액션아이템:'):
                    current_section = "actions"
                elif current_section == "actions" and line.startswith('-'):
                    action_item = line.replace('-', '').strip()
                    if action_item:
                        action_items.append(action_item)
            
            # 기본값 설정
            if not summary:
                summary = "오늘의 감정을 나누었어요"
            if not keywords:
                keywords = ["#감정나눔"]
            if not action_items:
                action_items = ["오늘도 고생 많았어요"]
            
            keywords = keywords[:5]
            action_items = action_items[:3]
            
            return {
                "summary": summary,
                "keywords": keywords,
                "action_items": action_items,
                "success": True
            }
            
        except Exception as e:
            print(f"대화 요약 생성 오류: {e}")
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

def check_content_with_local_model(text: str) -> dict:
    """로컬 모델을 사용한 콘텐츠 검사 (기본 키워드 검사 사용)"""
    if not text or not isinstance(text, str):
        return {
            "flagged": False,
            "self_harm": False,
            "violence": False,
            "error": "Empty or invalid text"
        }
    
    try:
        is_self_harm = check_harmful_content(text)
        is_violence = check_violence_content(text)
        
        return {
            "flagged": is_self_harm or is_violence,
            "self_harm": is_self_harm,
            "violence": is_violence,
            "success": True
        }
        
    except Exception as e:
        return {
            "flagged": check_harmful_content(text) or check_violence_content(text),
            "self_harm": check_harmful_content(text),
            "violence": check_violence_content(text),
            "error": str(e),
            "fallback": True
        }
