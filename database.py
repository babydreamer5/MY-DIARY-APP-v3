import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# ✅ SQLite 데이터베이스 설정 및 초기화
DB_PATH = "mindtalk_diary.db"

def init_database():
    """데이터베이스 초기화 및 테이블 생성"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 일기 테이블 생성
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS diary_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            mood TEXT NOT NULL,
            summary TEXT NOT NULL,
            keywords TEXT,
            suggested_keywords TEXT,
            action_items TEXT,
            chat_messages TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 휴지통 테이블 생성
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS deleted_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_id INTEGER,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            mood TEXT NOT NULL,
            summary TEXT NOT NULL,
            keywords TEXT,
            suggested_keywords TEXT,
            action_items TEXT,
            chat_messages TEXT,
            deleted_date TEXT NOT NULL,
            auto_delete_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 설정 테이블 생성
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 토큰 사용량 테이블 생성
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS token_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_tokens INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"데이터베이스 초기화 오류: {e}")
        return False

def save_diary_to_db(diary_entry):
    """일기를 데이터베이스에 저장"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO diary_entries 
        (date, time, mood, summary, keywords, suggested_keywords, action_items, chat_messages)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            diary_entry['date'],
            diary_entry['time'],
            diary_entry['mood'],
            diary_entry['summary'],
            json.dumps(diary_entry.get('keywords', []), ensure_ascii=False),
            json.dumps(diary_entry.get('suggested_keywords', []), ensure_ascii=False),
            json.dumps(diary_entry.get('action_items', []), ensure_ascii=False),
            json.dumps(diary_entry.get('chat_messages', []), ensure_ascii=False)
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"일기 저장 오류: {e}")
        return False

def load_diaries_from_db():
    """데이터베이스에서 모든 일기 불러오기"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT date, time, mood, summary, keywords, suggested_keywords, action_items, chat_messages
        FROM diary_entries 
        ORDER BY date, time
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        diaries = []
        for row in rows:
            diary = {
                'date': row[0],
                'time': row[1],
                'mood': row[2],
                'summary': row[3],
                'keywords': json.loads(row[4]) if row[4] else [],
                'suggested_keywords': json.loads(row[5]) if row[5] else [],
                'action_items': json.loads(row[6]) if row[6] else [],
                'chat_messages': json.loads(row[7]) if row[7] else []
            }
            diaries.append(diary)
        
        return diaries
    except Exception as e:
        print(f"일기 불러오기 오류: {e}")
        return []

def delete_diary_from_db(diary_entry):
    """데이터베이스에서 일기 삭제하고 휴지통으로 이동"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 원본 일기 찾기
        cursor.execute('''
        SELECT rowid FROM diary_entries 
        WHERE date = ? AND time = ? AND summary = ?
        ''', (diary_entry['date'], diary_entry['time'], diary_entry['summary']))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
        
        original_id = result[0]
        
        # 휴지통으로 이동
        deleted_date = datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')
        auto_delete_date = (datetime.now() + timedelta(days=30)).strftime('%Y년 %m월 %d일')
        
        cursor.execute('''
        INSERT INTO deleted_entries 
        (original_id, date, time, mood, summary, keywords, suggested_keywords, action_items, chat_messages, deleted_date, auto_delete_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            original_id,
            diary_entry['date'],
            diary_entry['time'],
            diary_entry['mood'],
            diary_entry['summary'],
            json.dumps(diary_entry.get('keywords', []), ensure_ascii=False),
            json.dumps(diary_entry.get('suggested_keywords', []), ensure_ascii=False),
            json.dumps(diary_entry.get('action_items', []), ensure_ascii=False),
            json.dumps(diary_entry.get('chat_messages', []), ensure_ascii=False),
            deleted_date,
            auto_delete_date
        ))
        
        # 원본에서 삭제
        cursor.execute('DELETE FROM diary_entries WHERE rowid = ?', (original_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"일기 삭제 오류: {e}")
        return False

def load_deleted_entries_from_db():
    """데이터베이스에서 휴지통 항목들 불러오기"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT date, time, mood, summary, keywords, suggested_keywords, action_items, chat_messages, deleted_date, auto_delete_date
        FROM deleted_entries 
        ORDER BY deleted_date DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        deleted_entries = []
        for row in rows:
            entry = {
                'date': row[0],
                'time': row[1],
                'mood': row[2],
                'summary': row[3],
                'keywords': json.loads(row[4]) if row[4] else [],
                'suggested_keywords': json.loads(row[5]) if row[5] else [],
                'action_items': json.loads(row[6]) if row[6] else [],
                'chat_messages': json.loads(row[7]) if row[7] else [],
                'deleted_date': row[8],
                'auto_delete_date': row[9]
            }
            deleted_entries.append(entry)
        
        return deleted_entries
    except Exception as e:
        print(f"휴지통 불러오기 오류: {e}")
        return []

def restore_from_trash_db(trash_entry):
    """휴지통에서 일기 복원"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 원본으로 복원
        cursor.execute('''
        INSERT INTO diary_entries 
        (date, time, mood, summary, keywords, suggested_keywords, action_items, chat_messages)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trash_entry['date'],
            trash_entry['time'],
            trash_entry['mood'],
            trash_entry['summary'],
            json.dumps(trash_entry.get('keywords', []), ensure_ascii=False),
            json.dumps(trash_entry.get('suggested_keywords', []), ensure_ascii=False),
            json.dumps(trash_entry.get('action_items', []), ensure_ascii=False),
            json.dumps(trash_entry.get('chat_messages', []), ensure_ascii=False)
        ))
        
        # 휴지통에서 삭제
        cursor.execute('''
        DELETE FROM deleted_entries 
        WHERE date = ? AND time = ? AND summary = ? AND deleted_date = ?
        ''', (trash_entry['date'], trash_entry['time'], trash_entry['summary'], trash_entry['deleted_date']))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"일기 복원 오류: {e}")
        return False

def permanent_delete_from_trash_db(trash_entry):
    """휴지통에서 영구 삭제"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        DELETE FROM deleted_entries 
        WHERE date = ? AND time = ? AND summary = ? AND deleted_date = ?
        ''', (trash_entry['date'], trash_entry['time'], trash_entry['summary'], trash_entry['deleted_date']))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"영구 삭제 오류: {e}")
        return False

def clean_expired_trash_db():
    """만료된 휴지통 항목 자동 삭제"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        # 만료된 항목들 찾기
        cursor.execute('SELECT auto_delete_date FROM deleted_entries')
        rows = cursor.fetchall()
        
        expired_dates = []
        for row in rows:
            try:
                auto_delete_date_str = row[0]
                auto_delete_date = datetime.strptime(auto_delete_date_str.replace('년 ', '-').replace('월 ', '-').replace('일', ''), '%Y-%m-%d').date()
                if auto_delete_date <= today:
                    expired_dates.append(auto_delete_date_str)
            except:
                continue
        
        # 만료된 항목들 삭제
        for expired_date in expired_dates:
            cursor.execute('DELETE FROM deleted_entries WHERE auto_delete_date = ?', (expired_date,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"휴지통 정리 오류: {e}")
        return False

def save_setting_to_db(key, value):
    """설정을 데이터베이스에 저장"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO app_settings (setting_key, setting_value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, str(value)))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"설정 저장 오류: {e}")
        return False

def load_setting_from_db(key, default_value):
    """데이터베이스에서 설정 불러오기"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT setting_value FROM app_settings WHERE setting_key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            return default_value
    except Exception as e:
        print(f"설정 불러오기 오류: {e}")
        return default_value

def save_token_usage_to_db(tokens):
    """토큰 사용량을 데이터베이스에 저장"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO token_usage (id, total_tokens, last_updated)
        VALUES (1, ?, CURRENT_TIMESTAMP)
        ''', (tokens,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"토큰 사용량 저장 오류: {e}")
        return False

def load_token_usage_from_db():
    """데이터베이스에서 토큰 사용량 불러오기"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT total_tokens FROM token_usage WHERE id = 1')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            return 0
    except Exception as e:
        print(f"토큰 사용량 불러오기 오류: {e}")
        return 0

# ✅ 데이터 저장/로딩 함수들
def save_data_to_db():
    """모든 세션 데이터를 SQLite에 저장"""
    import streamlit as st
    try:
        # 설정 저장
        save_setting_to_db('ai_name', st.session_state.get('ai_name', '루나'))
        save_setting_to_db('selected_theme', st.session_state.get('selected_theme', '라벤더'))
        save_setting_to_db('consecutive_days', st.session_state.get('consecutive_days', 0))
        save_setting_to_db('last_entry_date', st.session_state.get('last_entry_date', ''))
        
        # 토큰 사용량 저장
        save_token_usage_to_db(st.session_state.get('token_usage', 0))
        
        return True
    except Exception as e:
        print(f"데이터 저장 오류: {e}")
        return False

def load_data_from_db():
    """SQLite에서 모든 데이터 불러오기"""
    import streamlit as st
    try:
        # 일기 데이터 불러오기
        st.session_state.diary_entries = load_diaries_from_db()
        
        # 휴지통 데이터 불러오기
        st.session_state.deleted_entries = load_deleted_entries_from_db()
        
        # 설정 불러오기
        st.session_state.ai_name = load_setting_from_db('ai_name', '루나')
        st.session_state.selected_theme = load_setting_from_db('selected_theme', '라벤더')
        st.session_state.consecutive_days = int(load_setting_from_db('consecutive_days', 0))
        st.session_state.last_entry_date = load_setting_from_db('last_entry_date', '')
        
        # 토큰 사용량 불러오기
        st.session_state.token_usage = load_token_usage_from_db()
        
        return True
    except Exception as e:
        print(f"데이터 불러오기 오류: {e}")
        return False

# ✅ 일기 삭제 관련 유틸리티 함수들
def move_to_trash(diary_entry):
    """일기를 휴지통으로 이동 (SQLite 사용)"""
    import streamlit as st
    try:
        # SQLite에서 삭제하고 휴지통으로 이동
        if delete_diary_from_db(diary_entry):
            # 세션에서도 업데이트
            st.session_state.diary_entries = load_diaries_from_db()
            st.session_state.deleted_entries = load_deleted_entries_from_db()
            return True
        return False
    except Exception as e:
        print(f"일기 삭제 오류: {e}")
        return False

def restore_from_trash(trash_entry):
    """휴지통에서 일기 복원 (SQLite 사용)"""
    import streamlit as st
    try:
        if restore_from_trash_db(trash_entry):
            # 세션에서도 업데이트
            st.session_state.diary_entries = load_diaries_from_db()
            st.session_state.deleted_entries = load_deleted_entries_from_db()
            return True
        return False
    except Exception as e:
        print(f"일기 복원 오류: {e}")
        return False

def permanent_delete_from_trash(trash_entry):
    """휴지통에서 영구 삭제 (SQLite 사용)"""
    import streamlit as st
    try:
        if permanent_delete_from_trash_db(trash_entry):
            # 세션에서도 업데이트
            st.session_state.deleted_entries = load_deleted_entries_from_db()
            return True
        return False
    except Exception as e:
        print(f"영구 삭제 오류: {e}")
        return False

def clean_expired_trash():
    """30일 지난 휴지통 항목 자동 삭제 (SQLite 사용)"""
    import streamlit as st
    try:
        if clean_expired_trash_db():
            # 세션에서도 업데이트
            st.session_state.deleted_entries = load_deleted_entries_from_db()
        return True
    except Exception as e:
        print(f"휴지통 정리 오류: {e}")
        return False