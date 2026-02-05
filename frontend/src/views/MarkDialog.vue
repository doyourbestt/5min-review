<template>
  <div class="dialog-overlay" @click.self="$emit('close')">
    <div class="dialog">
      <div class="dialog-header">
        <h2>{{ isEdit ? '编辑标记' : '添加标记' }}</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div class="dialog-body">
        <div class="form-group">
          <label>日期</label>
          <input v-model="form.date" type="date" required>
        </div>

        <div class="form-group">
          <label>Markdown文本</label>
          <textarea
            v-model="form.markdown"
            placeholder="粘贴markdown格式的文本...

## 姓名
- 标签1：内容1
- 标签2：内容2

## 姓名2
- 标签1：内容1"
            rows="12"
          ></textarea>
        </div>

        <div v-if="parsedCards.length > 0" class="preview">
          <h3>预览 ({{ parsedCards.length }}张卡片)</h3>
          <div v-for="(card, index) in parsedCards" :key="index" class="preview-card">
            <div class="preview-header">
              <span class="name">{{ card.name }}</span>
              <span class="emoji">{{ card.emoji }}</span>
            </div>
            <div class="preview-content">{{ card.content.substring(0, 100) }}...</div>
          </div>
        </div>
        <div v-if="parseError" class="parse-error">
          {{ parseError }}
        </div>
        <div v-if="form.markdown.trim() && parsedCards.length === 0 && !parseError" class="parse-tip">
          正在解析...
        </div>
      </div>

      <div class="dialog-footer">
        <button class="btn" @click="$emit('close')">取消</button>
        <button
          class="btn btn-primary"
          :disabled="!canSave || isSubmitting"
          @click="handleSave"
        >
          {{ isSubmitting ? '保存中...' : '保存' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { parseMarkdown, saveCards, updateCard } from '../api'

const props = defineProps({
  card: Object
})

const emit = defineEmits(['close', 'save'])

const isEdit = computed(() => !!props.card?.id)

const form = ref({
  date: '',
  markdown: ''
})

const parsedCards = ref([])
const isSubmitting = ref(false)
const parseError = ref('')

const canSave = computed(() => {
  return form.value.date && form.value.markdown.trim()
})

const loadCardData = () => {
  if (props.card) {
    const nameEmoji = props.card.emoji
      ? `${props.card.name} ${props.card.emoji}`
      : props.card.name
    form.value = {
      date: props.card.date,
      markdown: `## ${nameEmoji}\n${props.card.content}`
    }
    parseCurrentMarkdown()
  } else {
    const today = new Date().toISOString().split('T')[0]
    form.value = {
      date: today,
      markdown: ''
    }
    parsedCards.value = []
  }
}

const parseCurrentMarkdown = async () => {
  if (!form.value.markdown.trim()) {
    parsedCards.value = []
    return
  }
  try {
    const res = await parseMarkdown(form.value.markdown)
    console.log('解析结果:', res)
    parsedCards.value = res.cards || []
    parseError.value = ''
  } catch (error) {
    console.error('解析失败:', error)
    parsedCards.value = []
    parseError.value = error.message || '解析失败，请检查格式'
  }
}

watch(() => form.value.markdown, () => {
  parseCurrentMarkdown()
})

const handleSave = async () => {
  if (!canSave.value || isSubmitting.value) return

  isSubmitting.value = true
  try {
    const data = {
      date: form.value.date,
      cards: parsedCards.value
    }

    if (isEdit.value) {
      await updateCard(props.card.id, {
        date: form.value.date,
        name: parsedCards.value[0]?.name || '',
        emoji: parsedCards.value[0]?.emoji || '',
        content: parsedCards.value[0]?.content || ''
      })
    } else {
      await saveCards(form.value.date, parsedCards.value)
    }

    emit('save')
  } catch (error) {
    alert(error.message || '保存失败')
  } finally {
    isSubmitting.value = false
  }
}

loadCardData()
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
  max-width: 600px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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
  overflow-y: auto;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--text-secondary);
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: 14px;
  font-family: inherit;
}

.form-group textarea {
  resize: vertical;
  font-family: monospace;
}

.preview {
  background: var(--bg-color);
  border-radius: var(--border-radius);
  padding: 16px;
  margin-top: 16px;
}

.preview h3 {
  margin: 0 0 12px;
  font-size: 14px;
  color: var(--text-secondary);
}

.preview-card {
  background: var(--card-bg);
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
}

.preview-card:last-child {
  margin-bottom: 0;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.preview-header .name {
  font-weight: 600;
}

.preview-header .emoji {
  font-size: 18px;
}

.preview-content {
  font-size: 13px;
  color: var(--text-tertiary);
  line-height: 1.5;
}

.parse-error {
  color: var(--error-color);
  font-size: 13px;
  margin-top: 12px;
  padding: 12px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 6px;
}

.parse-tip {
  color: var(--text-tertiary);
  font-size: 13px;
  margin-top: 12px;
  padding: 12px;
  background: var(--bg-color);
  border-radius: 6px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--border-color);
}

.dialog-footer .btn {
  padding: 10px 24px;
  border: 1px solid var(--border-color);
  background: none;
  border-radius: var(--border-radius);
  cursor: pointer;
}

.dialog-footer .btn-primary {
  background: var(--primary-color);
  color: white;
  border: none;
}

.dialog-footer .btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
