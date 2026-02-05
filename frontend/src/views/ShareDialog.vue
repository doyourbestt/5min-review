<template>
  <div class="dialog-overlay" @click.self="$emit('close')">
    <div class="dialog">
      <div class="dialog-header">
        <h2>分享标记</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div class="dialog-body">
        <div class="share-info">
          <p class="share-name">{{ card.name }} {{ card.emoji }}</p>
          <p class="share-date">{{ formatDate(card.date) }}</p>
        </div>

        <div class="share-link">
          <label>分享链接（只读）</label>
          <div class="link-input">
            <input readonly :value="shareUrl" ref="linkInput">
            <button class="copy-btn" @click="copyLink">
              {{ copied ? '已复制' : '复制链接' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  card: Object
})

const emit = defineEmits(['close'])

const copied = ref(false)
const linkInput = ref(null)

const shareUrl = computed(() => {
  if (!props.card?.share_token) return ''
  return `${window.location.origin}/#/share/${props.card.share_token}`
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
}

const copyLink = async () => {
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (error) {
    linkInput.value.select()
    document.execCommand('copy')
    copied.value = true
  }
}

onMounted(() => {
  console.log('Share URL:', shareUrl.value)
})
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.dialog {
  background: var(--card-bg);
  border-radius: var(--border-radius);
  width: 100%;
  max-width: 480px;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
}

.dialog-header h2 {
  margin: 0;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-tertiary);
}

.dialog-body {
  padding: 20px;
}

.share-info {
  text-align: center;
  margin-bottom: 24px;
}

.share-name {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 8px;
}

.share-date {
  color: var(--text-tertiary);
  font-size: 14px;
  margin: 0;
}

.share-link label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--text-secondary);
}

.link-input {
  display: flex;
  gap: 8px;
}

.link-input input {
  flex: 1;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: 14px;
  background: var(--bg-color);
}

.copy-btn {
  padding: 12px 20px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  font-size: 14px;
}

.copy-btn:hover {
  opacity: 0.9;
}
</style>
