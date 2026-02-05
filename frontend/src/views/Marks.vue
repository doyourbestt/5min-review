<template>
  <div class="marks-page">
    <div class="container">
      <header class="page-header">
        <button class="back-btn" @click="$router.back()">← 返回</button>
        <h1>复盘标记</h1>
        <button class="btn btn-primary" @click="showAddDialog = true">
          + 添加标记
        </button>
      </header>

      <div v-if="loading" class="loading">
        <p>加载中...</p>
      </div>

      <div v-else-if="cards.length === 0" class="empty-state">
        <p>暂无复盘标记</p>
        <button class="btn btn-primary" @click="showAddDialog =">
          添加第一个标记
        </button>
      </div>

      <div v-else class="marks-list">
        <div v-for="card in cards" :key="card.id" class="mark-card">
          <div class="card-header" @click="toggleCard(card.id)">
            <div class="card-title">
              <span class="name">{{ card.name }}</span>
              <span class="emoji">{{ card.emoji }}</span>
            </div>
            <div class="card-meta">
              <span class="date">{{ formatDate(card.date) }}</span>
              <span class="expand-icon">{{ expandedCards[card.id] ? '▼' : '▶' }}</span>
            </div>
          </div>
          <div v-show="expandedCards[card.id]" class="card-content">
            <div class="content-lines">
              <div v-for="(line, index) in parseContent(card.content)" :key="index" class="content-line">
                {{ line }}
              </div>
            </div>
            <div class="card-actions">
              <button class="btn-text" @click="editCard(card)">编辑</button>
              <button class="btn-text danger" @click="confirmDelete(card)">删除</button>
              <button class="btn-text" @click="shareCard(card)">分享</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <MarkDialog
      v-if="showAddDialog || editingCard"
      :card="editingCard"
      @close="closeDialog"
      @save="saveCard"
    />

    <ShareDialog
      v-if="sharingCard"
      :card="sharingCard"
      @close="sharingCard = null"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getMyCards, deleteCard } from '../api'
import MarkDialog from './MarkDialog.vue'
import ShareDialog from './ShareDialog.vue'

const cards = ref([])
const loading = ref(true)
const expandedCards = ref({})
const showAddDialog = ref(false)
const editingCard = ref(null)
const sharingCard = ref(null)

const loadCards = async () => {
  loading.value = true
  try {
    const res = await getMyCards()
    cards.value = res.cards || []
  } catch (error) {
    console.error('加载卡片失败:', error)
  } finally {
    loading.value = false
  }
}

const toggleCard = (cardId) => {
  expandedCards.value[cardId] = !expandedCards.value[cardId]
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

const parseContent = (content) => {
  if (!content) return []
  return content.split('\n').filter(line => line.trim())
}

const editCard = (card) => {
  editingCard.value = { ...card }
}

const closeDialog = () => {
  showAddDialog.value = false
  editingCard.value = null
  loadCards()
}

const saveCard = async () => {
  closeDialog()
}

const confirmDelete = async (card) => {
  if (confirm(`确定删除"${card.name}"的标记吗？`)) {
    try {
      await deleteCard(card.id)
      loadCards()
    } catch (error) {
      alert('删除失败')
    }
  }
}

const shareCard = (card) => {
  sharingCard.value = card
}

onMounted(() => {
  loadCards()
})
</script>

<style scoped>
.marks-page {
  min-height: 100vh;
  background: var(--bg-color);
  padding-bottom: 40px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 0;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 30px;
}

.back-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 14px;
}

.page-header h1 {
  font-size: 20px;
  margin: 0;
}

.loading,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-tertiary);
}

.marks-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mark-card {
  background: var(--card-bg);
  border-radius: var(--border-radius);
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.card-header:hover {
  background: var(--bg-color);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-title .name {
  font-size: 18px;
  font-weight: 600;
}

.card-title .emoji {
  font-size: 24px;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-tertiary);
  font-size: 14px;
}

.card-content {
  padding: 0 20px 20px;
  border-top: 1px solid var(--border-color);
}

.content-lines {
  padding: 16px 0;
}

.content-line {
  padding: 8px 0;
  color: var(--text-primary);
  line-height: 1.6;
  border-bottom: 1px dashed var(--border-color);
}

.content-line:last-child {
  border-bottom: none;
}

.card-actions {
  display: flex;
  gap: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.btn-text {
  background: none;
  border: none;
  color: var(--primary-color);
  cursor: pointer;
  font-size: 14px;
}

.btn-text.danger {
  color: var(--error-color);
}

.btn-text:hover {
  opacity: 0.8;
}
</style>
