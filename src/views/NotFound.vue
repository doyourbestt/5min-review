<template>
  <div class="not-found-page">
    <div class="content">
      <h1>404</h1>
      <p>页面不存在</p>
      <router-link to="/" class="btn btn-primary">返回首页</router-link>
    </div>
  </div>
</template>

<style scoped>
.not-found-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-color);
}

.content {
  text-align: center;
}

.content h1 {
  font-size: 120px;
  color: var(--primary-color);
  margin-bottom: 20px;
  font-weight: 700;
}

.content p {
  font-size: 24px;
  color: var(--text-secondary);
  margin-bottom: 40px;
}

.btn {
  padding: 12px 30px;
  font-size: 16px;
}
</style>
