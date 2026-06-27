"""
Flask主应用 - 提供API接口
"""
from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
from database import db
from video_parser import parse_video_api
import requests as http_requests
import os
import urllib.parse

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# API路由

@app.route('/api/chapters', methods=['GET'])
def get_chapters():
    """获取所有章节"""
    chapters = db.get_all_chapters()
    return jsonify({
        'success': True,
        'data': chapters
    })


@app.route('/api/chapters', methods=['POST'])
def create_chapter():
    """创建新章节"""
    data = request.json
    chapter_name = data.get('chapter_name')
    bv_number = data.get('bv_number')

    if not chapter_name or not bv_number:
        return jsonify({
            'success': False,
            'error': '章节名称和BV号不能为空'
        }), 400

    # 创建章节
    success = db.create_chapter(chapter_name, bv_number)

    if success:
        return jsonify({
            'success': True,
            'message': '章节创建成功'
        })
    else:
        return jsonify({
            'success': False,
            'error': '章节创建失败'
        }), 500


@app.route('/api/chapters/<chapter_name>', methods=['PUT'])
def update_chapter(chapter_name):
    """更新章节"""
    data = request.json
    new_name = data.get('new_name')
    bv_number = data.get('bv_number')

    success = db.update_chapter(chapter_name, new_name, bv_number)

    if success:
        return jsonify({
            'success': True
        })
    else:
        return jsonify({
            'success': False,
            'error': '章节更新失败'
        }), 500


@app.route('/api/chapters/<chapter_name>', methods=['DELETE'])
def delete_chapter(chapter_name):
    """删除章节"""
    success = db.delete_chapter(chapter_name)

    if success:
        return jsonify({
            'success': True
        })
    else:
        return jsonify({
            'success': False,
            'error': '章节删除失败'
        }), 500


@app.route('/api/chapters/<chapter_name>/sentences', methods=['GET'])
def get_sentences(chapter_name):
    """获取章节的句子列表"""
    sentences = db.get_sentences(chapter_name)
    return jsonify({
        'success': True,
        'data': sentences
    })


@app.route('/api/chapters/<chapter_name>/sentences', methods=['POST'])
def add_sentence(chapter_name):
    """添加句子到章节"""
    data = request.json
    sentence = data.get('sentence')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    note = data.get('note', '')

    if not sentence or not start_time or not end_time:
        return jsonify({
            'success': False,
            'error': '句子、开始时间和结束时间不能为空'
        }), 400

    success = db.add_sentence(chapter_name, sentence, start_time, end_time, note)

    if success:
        return jsonify({
            'success': True
        })
    else:
        return jsonify({
            'success': False,
            'error': '句子添加失败'
        }), 500


@app.route('/api/chapters/<chapter_name>/sentences/<int:index>', methods=['PUT'])
def update_sentence(chapter_name, index):
    """更新句子"""
    data = request.json
    success = db.update_sentence(
        chapter_name, index,
        data.get('sentence'),
        data.get('start_time'),
        data.get('end_time'),
        data.get('note')
    )

    if success:
        return jsonify({
            'success': True
        })
    else:
        return jsonify({
            'success': False,
            'error': '句子更新失败'
        }), 500


@app.route('/api/chapters/<chapter_name>/sentences/<int:index>', methods=['DELETE'])
def delete_sentence(chapter_name, index):
    """删除句子"""
    success = db.delete_sentence(chapter_name, index)

    if success:
        return jsonify({
            'success': True
        })
    else:
        return jsonify({
            'success': False,
            'error': '句子删除失败'
        }), 500


@app.route('/api/parse_video', methods=['POST'])
def parse_video():
    """解析B站视频获取直链"""
    data = request.json
    bv_number = data.get('bv_number')

    result = parse_video_api(bv_number)

    if result.get('success'):
        return jsonify(result)
    else:
        return jsonify(result), 500


@app.route('/api/audio_proxy')
def audio_proxy():
    """代理B站音频流，解决浏览器Referer限制"""
    audio_url = request.args.get('url')
    if not audio_url:
        return jsonify({'success': False, 'error': '缺少音频URL'}), 400

    try:
        # 添加必要的Referer和User-Agent请求B站资源
        headers = {
            'Referer': 'https://www.bilibili.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        # 支持 Range 请求（用于音频seek）
        range_header = request.headers.get('Range')
        if range_header:
            headers['Range'] = range_header

        resp = http_requests.get(audio_url, headers=headers, stream=True, timeout=30)

        # 构建响应，转发B站的流数据
        excluded_headers = ['transfer-encoding', 'connection']
        response_headers = {
            k: v for k, v in resp.raw.headers.items()
            if k.lower() not in excluded_headers
        }

        return Response(
            stream_with_context(resp.iter_content(chunk_size=8192)),
            status=resp.status_code,
            headers=response_headers
        )
    except Exception as e:
        print(f"音频代理失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Vercel部署入口
if __name__ == '__main__':
    app.run(debug=True)