"""
B站视频解析器 - 使用Bilibili API获取视频直链（含Wbi签名）
"""
import requests
import hashlib
import time
import urllib.parse
from typing import Optional, Dict


# Wbi签名混淆表
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52
]


def get_mixed_key(key: str) -> str:
    """根据混淆表生成32位mixed_key"""
    return ''.join(key[i] for i in MIXIN_KEY_ENC_TAB)[:32]


def sign_wbi(params: dict, img_key: str, sub_key: str) -> dict:
    """为请求参数添加Wbi签名"""
    mixin_key = get_mixed_key(img_key + sub_key)
    params = params.copy()
    params['wts'] = int(time.time())
    # 过滤非法字符并排序
    query = urllib.parse.urlencode({
        k: v for k, v in sorted(params.items())
        if isinstance(v, (str, int, float)) and not str(v).strip() == ''
    })
    params['w_rid'] = hashlib.md5((query + mixin_key).encode()).hexdigest()
    return params


class VideoParser:
    """B站视频解析器 - 使用Bilibili Web API"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        self._img_key = None
        self._sub_key = None
        self._key_time = 0

    def _get_wbi_keys(self):
        """从nav接口获取Wbi签名所需的img_key和sub_key"""
        # 缓存10分钟
        if self._img_key and time.time() - self._key_time < 600:
            return
        try:
            resp = self.session.get('https://api.bilibili.com/x/web-interface/nav')
            data = resp.json().get('data', {})
            wbi_img = data.get('wbi_img', {})
            img_url = wbi_img.get('img_url', '')
            sub_url = wbi_img.get('sub_url', '')
            self._img_key = img_url.split('/')[-1].split('.')[0]
            self._sub_key = sub_url.split('/')[-1].split('.')[0]
            self._key_time = time.time()
        except Exception as e:
            print(f"获取Wbi密钥失败: {e}")
            self._img_key = ''
            self._sub_key = ''

    def parse_bilibili_video(self, bv_number: str) -> Optional[Dict]:
        """
        解析B站视频获取直链

        Args:
            bv_number: B站视频BV号（如BV1xx411c7mD）

        Returns:
            包含视频URL和信息的字典
        """
        try:
            # 第一步：获取视频信息（cid, title, duration）
            video_info = self._get_video_info(bv_number)
            if not video_info:
                return {
                    'success': False,
                    'error': '获取视频信息失败',
                    'bv_number': bv_number
                }

            cid = video_info['cid']
            title = video_info['title']
            duration = video_info['duration']

            # 第二步：获取视频流地址
            play_url = self._get_play_url(bv_number, cid)
            if not play_url:
                return {
                    'success': False,
                    'error': '获取视频流地址失败',
                    'bv_number': bv_number
                }

            return {
                'success': True,
                'url': play_url,
                'title': title,
                'duration': duration,
                'bv_number': bv_number
            }

        except Exception as e:
            print(f"解析B站视频失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'bv_number': bv_number
            }

    def _get_video_info(self, bv_number: str) -> Optional[Dict]:
        """获取视频基本信息（cid, title, duration）"""
        try:
            resp = self.session.get(
                'https://api.bilibili.com/x/web-interface/view',
                params={'bvid': bv_number}
            )
            data = resp.json()
            if data.get('code') != 0:
                print(f"获取视频信息失败: {data.get('message', '未知错误')}")
                return None

            info = data['data']
            # 取第一个分P的cid
            cid = info['cid']
            title = info['title']
            duration = info['duration']

            return {
                'cid': cid,
                'title': title,
                'duration': duration
            }
        except Exception as e:
            print(f"获取视频信息异常: {e}")
            return None

    def _get_play_url(self, bv_number: str, cid: int) -> Optional[str]:
        """获取视频流播放地址"""
        try:
            # 获取Wbi密钥
            self._get_wbi_keys()

            params = {
                'bvid': bv_number,
                'cid': cid,
                'qn': 64,       # 720p
                'fnval': 16,    # 请求DASH格式
                'fourk': 0,
            }

            # 添加Wbi签名
            if self._img_key and self._sub_key:
                params = sign_wbi(params, self._img_key, self._sub_key)

            resp = self.session.get(
                'https://api.bilibili.com/x/player/wbi/playurl',
                params=params
            )
            data = resp.json()

            if data.get('code') != 0:
                print(f"获取播放地址失败: {data.get('message', '未知错误')}")
                # 尝试不带DASH的旧接口
                return self._get_play_url_fallback(bv_number, cid)

            # 优先取音频流URL（用于听力练习）
            dash = data['data'].get('dash', {})
            audio_list = dash.get('audio', [])
            if audio_list:
                # 取最高音质
                audio_list.sort(key=lambda x: x.get('bandwidth', 0), reverse=True)
                return audio_list[0]['baseUrl']

            # 如果没有独立音频流，取视频流（含音频）
            video_list = dash.get('video', [])
            if video_list:
                video_list.sort(key=lambda x: x.get('bandwidth', 0), reverse=True)
                return video_list[0]['baseUrl']

            # 回退到旧格式
            durl = data['data'].get('durl', [])
            if durl:
                return durl[0]['url']

            return None

        except Exception as e:
            print(f"获取播放地址异常: {e}")
            return self._get_play_url_fallback(bv_number, cid)

    def _get_play_url_fallback(self, bv_number: str, cid: int) -> Optional[str]:
        """回退方式获取播放地址（旧接口）"""
        try:
            resp = self.session.get(
                'https://api.bilibili.com/x/player/playurl',
                params={
                    'bvid': bv_number,
                    'cid': cid,
                    'qn': 64,
                    'otype': 'json',
                }
            )
            data = resp.json()
            if data.get('code') != 0:
                return None

            durl = data['data'].get('durl', [])
            if durl:
                return durl[0]['url']
            return None
        except Exception as e:
            print(f"回退获取播放地址失败: {e}")
            return None

    def parse_with_retry(self, bv_number: str, max_retry: int = 3) -> Optional[Dict]:
        """
        带重试机制的解析

        Args:
            bv_number: BV号
            max_retry: 最大重试次数

        Returns:
            解析结果
        """
        for attempt in range(max_retry):
            result = self.parse_bilibili_video(bv_number)
            if result and result.get('success'):
                return result
            if attempt < max_retry - 1:
                time.sleep(1)
        return result


# 全局解析器实例
parser = VideoParser()


def parse_video_api(bv_number: str) -> Dict:
    """
    API接口函数 - 解析视频

    Args:
        bv_number: BV号

    Returns:
        JSON响应字典
    """
    if not bv_number:
        return {
            'success': False,
            'error': 'BV号不能为空'
        }

    # 验证BV号格式（BV开头，长度约12位）
    if not bv_number.startswith('BV') or len(bv_number) < 10:
        return {
            'success': False,
            'error': 'BV号格式不正确'
        }

    result = parser.parse_with_retry(bv_number)
    return result
