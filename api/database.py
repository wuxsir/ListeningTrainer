"""
数据库管理模块 - 使用Supabase存储章节数据
"""
import os
from typing import List, Dict, Optional
from supabase import create_client, Client


class DatabaseManager:
    """Supabase数据库管理器"""

    def __init__(self):
        """初始化Supabase客户端"""
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)

    def create_chapter(self, chapter_name: str, bv_number: str) -> bool:
        """创建新章节"""
        try:
            self.supabase.table('chapters').insert({
                'chapter_name': chapter_name,
                'bv_number': bv_number
            }).execute()
            return True
        except Exception as e:
            print(f"创建章节失败: {e}")
            return False

    def get_all_chapters(self) -> List[Dict]:
        """获取所有章节"""
        try:
            response = self.supabase.table('chapters').select('*').order('created_at').execute()
            return response.data
        except Exception as e:
            print(f"获取章节失败: {e}")
            return []

    def get_chapter_by_name(self, chapter_name: str) -> Optional[Dict]:
        """根据名称获取章节"""
        try:
            response = self.supabase.table('chapters').select('*').eq('chapter_name', chapter_name).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"获取章节失败: {e}")
            return None

    def update_chapter(self, chapter_name: str, new_name: str = None,
                      bv_number: str = None) -> bool:
        """更新章节信息"""
        try:
            updates = {}
            if new_name:
                updates['chapter_name'] = new_name
            if bv_number:
                updates['bv_number'] = bv_number
            
            if not updates:
                return True
            
            self.supabase.table('chapters').update(updates).eq('chapter_name', chapter_name).execute()
            return True
        except Exception as e:
            print(f"更新章节失败: {e}")
            return False

    def delete_chapter(self, chapter_name: str) -> bool:
        """删除章节及其所有句子"""
        try:
            # 获取章节ID
            chapter = self.get_chapter_by_name(chapter_name)
            if not chapter:
                return False
            
            # 删除章节的句子（级联删除由数据库处理）
            # 删除章节
            self.supabase.table('chapters').delete().eq('chapter_name', chapter_name).execute()
            return True
        except Exception as e:
            print(f"删除章节失败: {e}")
            return False

    def add_sentence(self, chapter_name: str, sentence: str,
                    start_time: str, end_time: str, note: str = "") -> bool:
        """添加句子到章节"""
        try:
            # 获取章节ID
            chapter = self.get_chapter_by_name(chapter_name)
            if not chapter:
                return False
            
            self.supabase.table('sentences').insert({
                'chapter_id': chapter['id'],
                'sentence': sentence,
                'start_time': start_time,
                'end_time': end_time,
                'note': note
            }).execute()
            return True
        except Exception as e:
            print(f"添加句子失败: {e}")
            return False

    def get_sentences(self, chapter_name: str) -> List[Dict]:
        """获取章节的所有句子"""
        try:
            # 获取章节ID
            chapter = self.get_chapter_by_name(chapter_name)
            if not chapter:
                return []
            
            response = self.supabase.table('sentences').select('*').eq('chapter_id', chapter['id']).order('created_at').execute()
            return response.data
        except Exception as e:
            print(f"获取句子失败: {e}")
            return []

    def update_sentence(self, chapter_name: str, sentence_index: int,
                       sentence: str = None, start_time: str = None,
                       end_time: str = None, note: str = None) -> bool:
        """更新句子"""
        try:
            # 获取章节ID
            chapter = self.get_chapter_by_name(chapter_name)
            if not chapter:
                return False
            
            # 获取句子列表
            sentences = self.get_sentences(chapter_name)
            if sentence_index < 0 or sentence_index >= len(sentences):
                return False
            
            sentence_id = sentences[sentence_index]['id']
            
            updates = {}
            if sentence is not None:
                updates['sentence'] = sentence
            if start_time is not None:
                updates['start_time'] = start_time
            if end_time is not None:
                updates['end_time'] = end_time
            if note is not None:
                updates['note'] = note
            
            if not updates:
                return True
            
            self.supabase.table('sentences').update(updates).eq('id', sentence_id).execute()
            return True
        except Exception as e:
            print(f"更新句子失败: {e}")
            return False

    def delete_sentence(self, chapter_name: str, sentence_index: int) -> bool:
        """删除句子"""
        try:
            # 获取句子列表
            sentences = self.get_sentences(chapter_name)
            if sentence_index < 0 or sentence_index >= len(sentences):
                return False
            
            sentence_id = sentences[sentence_index]['id']
            
            self.supabase.table('sentences').delete().eq('id', sentence_id).execute()
            return True
        except Exception as e:
            print(f"删除句子失败: {e}")
            return False


# 全局数据库实例
db = DatabaseManager()