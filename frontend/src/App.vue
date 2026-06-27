<template>
  <div class="app-container">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <button @click="showCreateChapterDialog" class="btn-primary">新建章节</button>
      <button @click="showRenameChapterDialog" class="btn-secondary" :disabled="!currentChapter">重命名章节</button>
      <button @click="deleteCurrentChapter" class="btn-danger" :disabled="!currentChapter">删除章节</button>
      <button @click="showAddSentenceDialog" class="btn-secondary" :disabled="!currentChapter">添加句子</button>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧：章节列表 -->
      <div class="chapter-panel">
        <h3>章节列表</h3>
        <div class="chapter-list">
          <div 
            v-for="chapter in chapters" 
            :key="chapter.chapter_name"
            @click="selectChapter(chapter)"
            :class="{ active: currentChapter === chapter.chapter_name }"
            class="chapter-item"
          >
            {{ chapter.chapter_name }}
          </div>
        </div>
      </div>

      <!-- 右侧：句子列表和播放控制 -->
      <div class="content-panel">
        <!-- 句子列表 -->
        <div class="sentence-section">
          <h3>{{ currentChapter || '请选择章节' }}</h3>
          <div class="sentence-list" v-if="sentences.length > 0">
            <div v-for="(sentence, index) in sentences" :key="index" class="sentence-item">
              <div class="sentence-content">
                <p class="sentence-text">{{ sentence.sentence }}</p>
                <p class="sentence-time">{{ sentence.start_time }} - {{ sentence.end_time }}</p>
                <p v-if="sentence.note" class="sentence-note">备注: {{ sentence.note }}</p>
              </div>
              <div class="sentence-actions">
                <button @click="playSentence(index)" class="play-btn">播放</button>
                <button @click="showEditSentenceDialog(index)" class="edit-btn">编辑</button>
                <button @click="deleteSentence(index)" class="delete-btn">删除</button>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">暂无句子</div>
        </div>

        <!-- 播放控制 -->
        <div class="player-section" v-if="videoUrl">
          <div class="progress-bar">
            <span>{{ formatTime(currentTime) }}</span>
            <input type="range" v-model="progress" min="0" max="100" />
            <span>{{ formatTime(duration) }}</span>
          </div>
          <div class="controls">
            <button @click="togglePlay" class="control-btn">{{ isPlaying ? '暂停' : '播放' }}</button>
            <button @click="stop" class="control-btn">停止</button>
            <label>
              <input type="checkbox" v-model="loopMode" />
              循环播放
            </label>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建章节对话框 -->
    <div v-if="showCreateDialog" class="dialog-overlay">
      <div class="dialog">
        <h3>新建章节</h3>
        <input v-model="newChapterName" placeholder="章节名称" />
        <input v-model="newBvNumber" placeholder="B站BV号 (如BV123456789)" />
        <div class="dialog-buttons">
          <button @click="createChapter" class="btn-primary">创建</button>
          <button @click="closeCreateDialog" class="btn-secondary">取消</button>
        </div>
      </div>
    </div>

    <!-- 重命名章节对话框 -->
    <div v-if="showRenameDialog" class="dialog-overlay">
      <div class="dialog">
        <h3>重命名章节</h3>
        <input v-model="renameChapterName" placeholder="新章节名称" />
        <div class="dialog-buttons">
          <button @click="renameChapter" class="btn-primary">保存</button>
          <button @click="closeRenameDialog" class="btn-secondary">取消</button>
        </div>
      </div>
    </div>

    <!-- 添加句子对话框 -->
    <div v-if="showAddDialog" class="dialog-overlay">
      <div class="dialog">
        <h3>添加句子</h3>
        <textarea v-model="newSentence" placeholder="句子内容"></textarea>
        <input v-model="newStartTime" placeholder="开始时间 (00:00:00.000)" />
        <input v-model="newEndTime" placeholder="结束时间 (00:00:00.000)" />
        <input v-model="newNote" placeholder="备注" />
        <div class="dialog-buttons">
          <button @click="addSentence" class="btn-primary">添加</button>
          <button @click="closeAddDialog" class="btn-secondary">取消</button>
        </div>
      </div>
    </div>

    <!-- 编辑句子对话框 -->
    <div v-if="showEditDialog" class="dialog-overlay">
      <div class="dialog">
        <h3>编辑句子</h3>
        <textarea v-model="editSentenceText" placeholder="句子内容"></textarea>
        <input v-model="editStartTime" placeholder="开始时间 (00:00:00.000)" />
        <input v-model="editEndTime" placeholder="结束时间 (00:00:00.000)" />
        <input v-model="editNote" placeholder="备注" />
        <div class="dialog-buttons">
          <button @click="updateSentence" class="btn-primary">保存</button>
          <button @click="closeEditDialog" class="btn-secondary">取消</button>
        </div>
      </div>
    </div>

    <!-- 音频元素 -->
    <audio ref="audioPlayer" @timeupdate="updateProgress" @loadedmetadata="onAudioLoaded"></audio>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      chapters: [],
      currentChapter: null,
      sentences: [],
      videoUrl: null,
      bvNumber: null,
      
      // 播放状态
      isPlaying: false,
      currentTime: 0,
      duration: 0,
      progress: 0,
      loopMode: false,
      currentStartMs: 0,
      currentEndMs: 0,

      // 对话框状态
      showCreateDialog: false,
      showRenameDialog: false,
      showAddDialog: false,
      showEditDialog: false,
      
      // 新建章节
      newChapterName: '',
      newBvNumber: '',
      
      // 重命名章节
      renameChapterName: '',
      
      // 添加句子
      newSentence: '',
      newStartTime: '',
      newEndTime: '',
      newNote: '',
      
      // 编辑句子
      editSentenceIndex: -1,
      editSentenceText: '',
      editStartTime: '',
      editEndTime: '',
      editNote: ''
    }
  },
  mounted() {
    this.loadChapters()
  },
  methods: {
    // 加载章节列表
    async loadChapters() {
      try {
        const response = await axios.get('/api/chapters')
        this.chapters = response.data.data
      } catch (error) {
        console.error('加载章节失败:', error)
      }
    },

    // 选择章节
    async selectChapter(chapter) {
      this.currentChapter = chapter.chapter_name
      this.bvNumber = chapter.bv_number
      
      // 加载句子
      await this.loadSentences()
      
      // 解析视频URL
      if (this.bvNumber) {
        await this.parseVideo()
      }
    },

    // 加载句子
    async loadSentences() {
      try {
        const response = await axios.get(`/api/chapters/${this.currentChapter}/sentences`)
        this.sentences = response.data.data
      } catch (error) {
        console.error('加载句子失败:', error)
        this.sentences = []
      }
    },

    // 解析视频URL
    async parseVideo() {
      try {
        const response = await axios.post('/api/parse_video', {
          bv_number: this.bvNumber
        })
        
        if (response.data.success) {
          this.videoUrl = response.data.url
          // 通过后端代理播放，解决B站Referer限制
          const proxyUrl = '/api/audio_proxy?url=' + encodeURIComponent(this.videoUrl)
          this.$refs.audioPlayer.src = proxyUrl
        } else {
          alert('视频解析失败: ' + response.data.error)
        }
      } catch (error) {
        console.error('解析视频失败:', error)
        alert('解析视频失败，请检查BV号')
      }
    },

    // 播放句子片段
    playSentence(index) {
      const sentence = this.sentences[index]
      this.currentStartMs = this.timeStrToMs(sentence.start_time)
      this.currentEndMs = this.timeStrToMs(sentence.end_time)
      
      this.$refs.audioPlayer.currentTime = this.currentStartMs / 1000
      this.$refs.audioPlayer.play()
      this.isPlaying = true
    },

    // 时间字符串转毫秒
    timeStrToMs(timeStr) {
      const parts = timeStr.split(':')
      if (parts.length === 3) {
        const hours = parseInt(parts[0])
        const minutes = parseInt(parts[1])
        const secondsParts = parts[2].split('.')
        const seconds = parseInt(secondsParts[0])
        const ms = parseInt(secondsParts[1]) || 0
        return (hours * 3600 + minutes * 60 + seconds) * 1000 + ms
      } else if (parts.length === 2) {
        const minutes = parseInt(parts[0])
        const secondsParts = parts[1].split('.')
        const seconds = parseInt(secondsParts[0])
        const ms = parseInt(secondsParts[1]) || 0
        return (minutes * 60 + seconds) * 1000 + ms
      }
      return 0
    },

    // 格式化时间
    formatTime(seconds) {
      const h = Math.floor(seconds / 3600)
      const m = Math.floor((seconds % 3600) / 60)
      const s = Math.floor(seconds % 60)
      return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
    },

    // 更新播放进度
    updateProgress() {
      this.currentTime = this.$refs.audioPlayer.currentTime
      
      // 检查是否到达片段结束时间
      if (this.currentEndMs > 0 && this.currentTime >= this.currentEndMs / 1000) {
        if (this.loopMode) {
          this.$refs.audioPlayer.currentTime = this.currentStartMs / 1000
        } else {
          this.$refs.audioPlayer.pause()
          this.isPlaying = false
        }
      }
      
      this.progress = (this.currentTime / this.duration) * 100
    },

    // 音频加载完成
    onAudioLoaded() {
      this.duration = this.$refs.audioPlayer.duration
    },

    // 切换播放/暂停
    togglePlay() {
      if (this.isPlaying) {
        this.$refs.audioPlayer.pause()
      } else {
        this.$refs.audioPlayer.play()
      }
      this.isPlaying = !this.isPlaying
    },

    // 停止播放
    stop() {
      this.$refs.audioPlayer.pause()
      this.$refs.audioPlayer.currentTime = 0
      this.isPlaying = false
      this.currentStartMs = 0
      this.currentEndMs = 0
    },

    // ========== 章节操作 ==========

    // 显示创建章节对话框
    showCreateChapterDialog() {
      this.showCreateDialog = true
    },

    // 关闭创建章节对话框
    closeCreateDialog() {
      this.showCreateDialog = false
      this.newChapterName = ''
      this.newBvNumber = ''
    },

    // 创建章节
    async createChapter() {
      if (!this.newChapterName || !this.newBvNumber) {
        alert('请填写完整信息')
        return
      }

      try {
        await axios.post('/api/chapters', {
          chapter_name: this.newChapterName,
          bv_number: this.newBvNumber
        })
        
        this.closeCreateDialog()
        this.loadChapters()
      } catch (error) {
        alert('创建失败: ' + error.response?.data?.error)
      }
    },

    // 显示重命名章节对话框
    showRenameChapterDialog() {
      if (!this.currentChapter) return
      this.renameChapterName = this.currentChapter
      this.showRenameDialog = true
    },

    // 关闭重命名章节对话框
    closeRenameDialog() {
      this.showRenameDialog = false
      this.renameChapterName = ''
    },

    // 重命名章节
    async renameChapter() {
      if (!this.renameChapterName || this.renameChapterName === this.currentChapter) {
        this.closeRenameDialog()
        return
      }

      try {
        await axios.put(`/api/chapters/${this.currentChapter}`, {
          new_name: this.renameChapterName
        })
        
        this.currentChapter = this.renameChapterName
        this.closeRenameDialog()
        this.loadChapters()
      } catch (error) {
        alert('重命名失败: ' + error.response?.data?.error)
      }
    },

    // 删除当前章节
    async deleteCurrentChapter() {
      if (!this.currentChapter) return
      
      if (!confirm(`确定删除章节"${this.currentChapter}"吗?`)) return
      
      try {
        await axios.delete(`/api/chapters/${this.currentChapter}`)
        this.currentChapter = null
        this.sentences = []
        this.videoUrl = null
        this.loadChapters()
      } catch (error) {
        alert('删除失败')
      }
    },

    // ========== 句子操作 ==========

    // 显示添加句子对话框
    showAddSentenceDialog() {
      this.showAddDialog = true
    },

    // 关闭添加句子对话框
    closeAddDialog() {
      this.showAddDialog = false
      this.newSentence = ''
      this.newStartTime = '00:00:00.000'
      this.newEndTime = '00:00:00.000'
      this.newNote = ''
    },

    // 添加句子
    async addSentence() {
      if (!this.newSentence || !this.newStartTime || !this.newEndTime) {
        alert('请填写完整信息')
        return
      }

      try {
        await axios.post(`/api/chapters/${this.currentChapter}/sentences`, {
          sentence: this.newSentence,
          start_time: this.newStartTime,
          end_time: this.newEndTime,
          note: this.newNote
        })
        
        this.closeAddDialog()
        this.loadSentences()
      } catch (error) {
        alert('添加失败: ' + error.response?.data?.error)
      }
    },

    // 显示编辑句子对话框
    showEditSentenceDialog(index) {
      const sentence = this.sentences[index]
      this.editSentenceIndex = index
      this.editSentenceText = sentence.sentence
      this.editStartTime = sentence.start_time
      this.editEndTime = sentence.end_time
      this.editNote = sentence.note || ''
      this.showEditDialog = true
    },

    // 关闭编辑句子对话框
    closeEditDialog() {
      this.showEditDialog = false
      this.editSentenceIndex = -1
      this.editSentenceText = ''
      this.editStartTime = ''
      this.editEndTime = ''
      this.editNote = ''
    },

    // 更新句子
    async updateSentence() {
      if (!this.editSentenceText || !this.editStartTime || !this.editEndTime) {
        alert('请填写完整信息')
        return
      }

      try {
        await axios.put(`/api/chapters/${this.currentChapter}/sentences/${this.editSentenceIndex}`, {
          sentence: this.editSentenceText,
          start_time: this.editStartTime,
          end_time: this.editEndTime,
          note: this.editNote
        })
        
        this.closeEditDialog()
        this.loadSentences()
      } catch (error) {
        alert('更新失败: ' + error.response?.data?.error)
      }
    },

    // 删除句子
    async deleteSentence(index) {
      if (!confirm('确定删除这条句子吗?')) return

      try {
        await axios.delete(`/api/chapters/${this.currentChapter}/sentences/${index}`)
        this.loadSentences()
      } catch (error) {
        alert('删除失败')
      }
    }
  }
}
</script>

<style>
/* 基础样式 - 响应式设计 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app-container {
  font-family: 'Microsoft YaHei', Arial, sans-serif;
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

/* 工具栏 */
.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
  flex-wrap: wrap;
}

.btn-primary {
  padding: 8px 16px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-secondary {
  padding: 8px 16px;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-danger {
  padding: 8px 16px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-danger:disabled, .btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 主内容区 */
.main-content {
  display: flex;
  gap: 20px;
  min-height: 600px;
}

/* 章节面板 */
.chapter-panel {
  flex: 1;
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.chapter-panel h3 {
  margin-bottom: 15px;
}

.chapter-list {
  max-height: 500px;
  overflow-y: auto;
}

.chapter-item {
  padding: 10px;
  margin-bottom: 5px;
  background: #f9f9f9;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.chapter-item:hover {
  background: #e3f2fd;
}

.chapter-item.active {
  background: #4CAF50;
  color: white;
}

/* 内容面板 */
.content-panel {
  flex: 3;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sentence-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.sentence-section h3 {
  margin-bottom: 15px;
}

.sentence-list {
  max-height: 400px;
  overflow-y: auto;
}

.sentence-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 15px;
  margin-bottom: 10px;
  background: #f9f9f9;
  border-radius: 4px;
  gap: 10px;
}

.sentence-content {
  flex: 1;
  min-width: 0;
}

.sentence-text {
  margin-bottom: 5px;
  font-size: 16px;
  word-break: break-all;
}

.sentence-time {
  color: #666;
  font-size: 14px;
  margin-bottom: 3px;
}

.sentence-note {
  color: #888;
  font-size: 13px;
  font-style: italic;
}

.sentence-actions {
  display: flex;
  gap: 5px;
  flex-shrink: 0;
}

.play-btn {
  padding: 6px 12px;
  background: #FF9800;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.edit-btn {
  padding: 6px 12px;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.delete-btn {
  padding: 6px 12px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.empty-state {
  padding: 20px;
  text-align: center;
  color: #999;
}

/* 播放控制 */
.player-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.progress-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.progress-bar input[type="range"] {
  flex: 1;
}

.controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.control-btn {
  padding: 10px 20px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* 对话框 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  padding: 20px;
  border-radius: 8px;
  min-width: 300px;
  max-width: 500px;
  width: 90%;
}

.dialog h3 {
  margin-bottom: 15px;
}

.dialog input, .dialog textarea {
  width: 100%;
  padding: 10px;
  margin-bottom: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.dialog textarea {
  min-height: 80px;
  resize: vertical;
}

.dialog-buttons {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 10px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }
  
  .chapter-panel, .content-panel {
    width: 100%;
  }
  
  .toolbar {
    flex-wrap: wrap;
  }
  
  .sentence-item {
    flex-direction: column;
    gap: 10px;
  }
  
  .sentence-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .controls {
    flex-wrap: wrap;
  }
}
</style>