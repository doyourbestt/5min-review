<template>
  <div class="templates-page">
    <div class="container">
      <header class="page-header">
        <button class="back-btn" @click="$router.push('/')">← 返回首页</button>
        <h1>模板管理</h1>
        <button class="btn btn-primary" @click="showCreateModal = true">
          + 新建模板
        </button>
      </header>

      <!-- 模板列表 -->
      <section class="templates-list">
        <div v-for="template in templates" :key="template.id" class="template-card card">
          <div class="template-header">
            <h3>{{ template.name }}</h3>
            <div class="badges">
              <span v-if="template.isSystem" class="badge system">系统</span>
              <span v-if="template.isPublic" class="badge public">公开</span>
              <span class="badge type">{{ templateTypeText(template.templateType) }}</span>
            </div>
          </div>
          <p class="description">{{ template.description || '暂无描述' }}</p>
          <div class="template-meta">
            <span>{{ template.fieldCount }} 个字段</span>
            <span>使用 {{ template.useCount }} 次</span>
          </div>
          <div class="template-actions" v-if="!template.isSystem">
            <button class="btn-text" @click="editTemplate(template)">编辑</button>
            <button class="btn-text danger" @click="deleteTemplate(template.id)">删除</button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getTemplates, deleteTemplate as deleteTemplateApi } from '@api'

const templates = ref([])
const showCreateModal = ref(false)

const templateTypeText = (type) => {
  const map = {
    'daily': '每日',
    'weekly': '每周',
    'project': '项目',
    'custom': '自定义'
  }
  return map[type] || type
}

const loadTemplates = async () => {
  try {
    const res = await getTemplates()
    templates.value = res.data?.templates || []
  } catch (error) {
    console.error('获取模板失败:', error)
  }
}

const deleteTemplate = async (id) => {
  if (!confirm('确定要删除此模板吗？')) return
  try {
    await deleteTemplateApi(id)
    await loadTemplates()
  } catch (error) {
    alert('删除失败')
  }
}

const editTemplate = (template) => {
  // TODO: 打开编辑弹窗
  console.log('编辑模板:', template)
}

onMounted(loadTemplates)
</script>

<style scoped>
.templates-page {
  min-height: 100vh;
  background: var(--bg-color);
  padding-bottom: 40px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 30px;
}

.back-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
}

.templates-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.template-card {
  padding: 24px;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.template-header h3 {
  font-size: 18px;
  margin: 0;
}

.badges {
  display: flex;
  gap: 6px;
}

.badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.badge.system {
  background: #e3f2fd;
  color: #1976d2;
}

.badge.public {
  background: #e8f5e9;
  color: #388e3c;
}

.badge.type {
  background: var(--bg-color);
  color: var(--text-tertiary);
}

.description {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 16px;
  min-height: 40px;
}

.template-meta {
  display: flex;
  gap: 20px;
  color: var(--text-tertiary);
  font-size: 13px;
  margin-bottom: 16px;
}

.template-actions {
  display: flex;
  gap: 12px;
  padding-top: 16px;
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
</style>
