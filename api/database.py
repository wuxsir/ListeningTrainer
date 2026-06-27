"""
数据库管理模块 - 使用SQLite存储章节数据
"""
import sqlite3
import json
from typing import List, Dict, Optional
import os


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = "data.db"):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建章节表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_name TEXT UNIQUE NOT NULL,
                bv_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建句子表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_id INTEGER NOT NULL,
                sentence TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chapter_id) REFERENCES chapters (id)
            )
        ''')

        conn.commit()
        conn.close()

    def create_chapter(self, chapter_name: str, bv_number: str) -> bool:
        """
        创建新章节

        Args:
            chapter_name: 章节名称
            bv_number: B站视频BV号

        Returns:
            创建是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                'INSERT INTO chapters (chapter_name, bv_number) VALUES (?, ?)',
                (chapter_name, bv_number)
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"创建章节失败: {e}")
            return False

    def get_all_chapters(self) -> List[Dict]:
        """
        获取所有章节

        Returns:
            章节列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id, chapter_name, bv_number FROM chapters ORDER BY created_at')
        rows = cursor.fetchall()

        chapters = []
        for row in rows:
            chapters.append({
                'id': row[0],
                'chapter_name': row[1],
                'bv_number': row[2]
            })

        conn.close()
        return chapters

    def get_chapter_by_name(self, chapter_name: str) -> Optional[Dict]:
        """
        根据名称获取章节

        Args:
            chapter_name: 章节名称

        Returns:
            章节信息
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT id, chapter_name, bv_number FROM chapters WHERE chapter_name = ?',
            (chapter_name,)
        )
        row = cursor.fetchone()

        conn.close()

        if row:
            return {
                'id': row[0],
                'chapter_name': row[1],
                'bv_number': row[2]
            }
        return None

    def update_chapter(self, chapter_name: str, new_name: str = None,
                      bv_number: str = None) -> bool:
        """
        更新章节信息

        Args:
            chapter_name: 原章节名
            new_name: 新章节名（可选）
            bv_number: 新BV号（可选）

        Returns:
            更新是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if new_name:
                cursor.execute(
                    'UPDATE chapters SET chapter_name = ?, updated_at = CURRENT_TIMESTAMP WHERE chapter_name = ?',
                    (new_name, chapter_name)
                )

            if bv_number:
                cursor.execute(
                    'UPDATE chapters SET bv_number = ?, updated_at = CURRENT_TIMESTAMP WHERE chapter_name = ?',
                    (bv_number, chapter_name if not new_name else new_name)
                )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"更新章节失败: {e}")
            return False

    def delete_chapter(self, chapter_name: str) -> bool:
        """
        删除章节及其所有句子

        Args:
            chapter_name: 章节名称

        Returns:
            删除是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 先删除章节的所有句子
            cursor.execute(
                'DELETE FROM sentences WHERE chapter_id = (SELECT id FROM chapters WHERE chapter_name = ?)',
                (chapter_name,)
            )

            # 删除章节
            cursor.execute(
                'DELETE FROM chapters WHERE chapter_name = ?',
                (chapter_name,)
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"删除章节失败: {e}")
            return False

    def add_sentence(self, chapter_name: str, sentence: str,
                    start_time: str, end_time: str, note: str = "") -> bool:
        """
        添加句子到章节

        Args:
            chapter_name: 章节名称
            sentence: 句子文本
            start_time: 开始时间
            end_time: 结束时间
            note: 备注

        Returns:
            添加是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取章节ID
            cursor.execute(
                'SELECT id FROM chapters WHERE chapter_name = ?',
                (chapter_name,)
            )
            chapter_id = cursor.fetchone()

            if not chapter_id:
                conn.close()
                return False

            # 添加句子
            cursor.execute(
                'INSERT INTO sentences (chapter_id, sentence, start_time, end_time, note) VALUES (?, ?, ?, ?, ?)',
                (chapter_id[0], sentence, start_time, end_time, note)
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加句子失败: {e}")
            return False

    def get_sentences(self, chapter_name: str) -> List[Dict]:
        """
        获取章节的所有句子

        Args:
            chapter_name: 章节名称

        Returns:
            句子列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT s.sentence, s.start_time, s.end_time, s.note FROM sentences s '
            'JOIN chapters c ON s.chapter_id = c.id WHERE c.chapter_name = ? '
            'ORDER BY s.created_at',
            (chapter_name,)
        )
        rows = cursor.fetchall()

        sentences = []
        for row in rows:
            sentences.append({
                'sentence': row[0],
                'start_time': row[1],
                'end_time': row[2],
                'note': row[3]
            })

        conn.close()
        return sentences

    def update_sentence(self, chapter_name: str, sentence_index: int,
                       sentence: str = None, start_time: str = None,
                       end_time: str = None, note: str = None) -> bool:
        """
        更新句子

        Args:
            chapter_name: 章节名称
            sentence_index: 句子索引
            sentence: 新句子文本
            start_time: 新开始时间
            end_time: 新结束时间
            note: 新备注

        Returns:
            更新是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取句子ID
            cursor.execute(
                'SELECT s.id FROM sentences s '
                'JOIN chapters c ON s.chapter_id = c.id WHERE c.chapter_name = ? '
                'ORDER BY s.created_at LIMIT 1 OFFSET ?',
                (chapter_name, sentence_index)
            )
            sentence_id = cursor.fetchone()

            if not sentence_id:
                conn.close()
                return False

            # 构建更新SQL
            updates = []
            params = []

            if sentence:
                updates.append('sentence = ?')
                params.append(sentence)
            if start_time:
                updates.append('start_time = ?')
                params.append(start_time)
            if end_time:
                updates.append('end_time = ?')
                params.append(end_time)
            if note:
                updates.append('note = ?')
                params.append(note)

            if not updates:
                conn.close()
                return True

            params.append(sentence_id[0])
            sql = f'UPDATE sentences SET {", ".join(updates)} WHERE id = ?'

            cursor.execute(sql, params)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"更新句子失败: {e}")
            return False

    def delete_sentence(self, chapter_name: str, sentence_index: int) -> bool:
        """
        删除句子

        Args:
            chapter_name: 章节名称
            sentence_index: 句子索引

        Returns:
            删除是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取句子ID
            cursor.execute(
                'SELECT s.id FROM sentences s '
                'JOIN chapters c ON s.chapter_id = c.id WHERE c.chapter_name = ? '
                'ORDER BY s.created_at LIMIT 1 OFFSET ?',
                (chapter_name, sentence_index)
            )
            sentence_id = cursor.fetchone()

            if not sentence_id:
                conn.close()
                return False

            # 删除句子
            cursor.execute('DELETE FROM sentences WHERE id = ?', (sentence_id[0]))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"删除句子失败: {e}")
            return False


# 全局数据库实例
db = DatabaseManager()