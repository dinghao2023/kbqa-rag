<script setup lang="ts">
import { computed, ref } from 'vue'

const API_BASE = 'http://127.0.0.1:8000'

const file = ref<File | null>(null)
const dragging = ref(false)
const question = ref('')
const answer = ref('')
const sources = ref<string[]>([])
const uploadLoading = ref(false)
const askLoading = ref(false)
const uploadMsg = ref('')
const uploadError = ref(false)
const answerError = ref(false)

const fileSize = computed(() => {
  if (!file.value) return ''
  const kb = file.value.size / 1024
  if (kb < 1024) return `${Math.max(1, Math.round(kb))} KB`
  return `${(kb / 1024).toFixed(1)} MB`
})

const takeFile = (next: File | null) => {
  if (!next) {
    file.value = null
    return
  }
  if (!next.name.toLowerCase().endsWith('.pdf')) {
    file.value = null
    uploadError.value = true
    uploadMsg.value = '请上传 PDF 文件'
    return
  }
  file.value = next
  uploadMsg.value = ''
  uploadError.value = false
}

const onFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  takeFile(target.files?.[0] ?? null)
}

const onDrop = (e: DragEvent) => {
  dragging.value = false
  takeFile(e.dataTransfer?.files?.[0] ?? null)
}

const handleUpload = async () => {
  if (!file.value) return
  uploadLoading.value = true
  uploadMsg.value = ''
  uploadError.value = false
  try {
    const form = new FormData()
    form.append('file', file.value)
    const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: form })
    const data = await res.json()
    if (!res.ok) {
      uploadError.value = true
      uploadMsg.value = '上传失败，请确认文件是可复制文字的 PDF'
      return
    }
    uploadMsg.value = `已解析 ${data.filename}，生成 ${data.chunks} 个文本块`
  } catch {
    uploadError.value = true
    uploadMsg.value = '上传失败，请确认后端服务已启动'
  } finally {
    uploadLoading.value = false
  }
}

const handleAsk = async () => {
  if (!question.value.trim()) return
  askLoading.value = true
  answer.value = ''
  sources.value = []
  answerError.value = false
  try {
    const res = await fetch(`${API_BASE}/ask?question=${encodeURIComponent(question.value)}`)
    const data = await res.json()
    if (!res.ok || !data.answer) {
      answerError.value = true
      answer.value = '暂时无法回答，请确认文档已入库且后端服务正常'
      return
    }
    answer.value = data.answer
    sources.value = data.sources || []
  } catch {
    answerError.value = true
    answer.value = '请求失败，请确认后端服务已启动'
  } finally {
    askLoading.value = false
  }
}
</script>

<template>
  <div class="page">
    <header class="hero">
      <div class="brand">
        <span class="logo" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path
              d="M6.5 3.5h7.2L19 8.8V20a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 5 20V5a1.5 1.5 0 0 1 1.5-1.5Z"
              stroke="currentColor"
              stroke-width="1.6"
            />
            <path d="M13.5 3.8V8.2H18" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" />
            <path d="M8.2 12.2h7.6M8.2 15.4h5.4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
          </svg>
        </span>
        <div>
          <p class="eyebrow">个人知识库</p>
          <h1>kbqa-rag</h1>
        </div>
      </div>
      <p class="lead">上传 PDF，用自然语言提问。回答只依据文档内容，并标出来源。</p>
    </header>

    <main class="stack">
      <section class="panel">
        <div class="panel-head">
          <span class="step">01</span>
          <div>
            <h2>上传文档</h2>
            <p>仅支持带文字层的 PDF</p>
          </div>
        </div>

        <label
          class="drop"
          :class="{ 'is-drag': dragging, 'has-file': file }"
          @dragover.prevent="dragging = true"
          @dragleave.prevent="dragging = false"
          @drop.prevent="onDrop"
        >
          <input type="file" accept="application/pdf,.pdf" @change="onFileChange" />
          <span class="drop-title">{{ file ? file.name : '点击或拖入 PDF' }}</span>
          <span class="drop-hint">{{ file ? fileSize : '一次上传一份文档，同名文件会覆盖旧内容' }}</span>
        </label>

        <div class="actions">
          <button type="button" :disabled="!file || uploadLoading" @click="handleUpload">
            {{ uploadLoading ? '解析中…' : '解析并入库' }}
          </button>
        </div>
        <p v-if="uploadMsg" class="note" :class="uploadError ? 'is-error' : 'is-ok'">{{ uploadMsg }}</p>
      </section>

      <section class="panel">
        <div class="panel-head">
          <span class="step">02</span>
          <div>
            <h2>向知识库提问</h2>
            <p>按 Enter 发送</p>
          </div>
        </div>

        <div class="composer">
          <input
            v-model="question"
            placeholder="例如：文档里是怎么解释 any 类型的？"
            @keyup.enter="handleAsk"
          />
          <button type="button" :disabled="askLoading || !question.trim()" @click="handleAsk">
            {{ askLoading ? '生成中…' : '提问' }}
          </button>
        </div>

        <div class="answer" :class="{ 'is-error': answerError }" aria-live="polite">
          <template v-if="askLoading">
            <span class="bar"></span>
            <span class="bar short"></span>
            <p class="placeholder">正在根据文档生成回答…</p>
          </template>
          <template v-else-if="answer">
            <p class="answer-text">{{ answer }}</p>
            <div v-if="sources.length" class="sources">
              <span v-for="source in sources" :key="source" class="source">{{ source }}</span>
            </div>
          </template>
          <p v-else class="placeholder">回答会显示在这里，并附上引用的文档名。</p>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.page {
  width: min(760px, 100%);
  margin: 0 auto;
  padding: 56px 20px 80px;
}

.hero {
  margin-bottom: 28px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  color: #f4fff8;
  background: linear-gradient(160deg, #2f8a62, var(--accent-dark));
  box-shadow: 0 8px 18px rgba(31, 107, 74, 0.22);
}

.logo svg {
  width: 26px;
  height: 26px;
}

.eyebrow {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--accent);
}

h1 {
  margin: 1px 0 0;
  font-size: 34px;
  line-height: 1.1;
  letter-spacing: -0.04em;
  font-weight: 600;
}

.lead {
  margin: 14px 0 0;
  max-width: 42em;
  color: var(--muted);
  line-height: 1.65;
}

.stack {
  display: grid;
  gap: 16px;
}

.panel {
  background: var(--surface);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 20px;
  padding: 22px;
  box-shadow:
    0 1px 2px rgba(28, 25, 23, 0.04),
    0 16px 40px rgba(28, 25, 23, 0.06);
}

.panel-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.panel-head h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.panel-head p {
  margin: 2px 0 0;
  color: var(--muted);
  font-size: 13px;
}

.step {
  flex: none;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-radius: 999px;
  padding: 6px 9px;
}

.drop {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-start;
  border: 1.5px dashed #d9d3c8;
  border-radius: 16px;
  padding: 22px 18px;
  background: #faf8f4;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease, transform 0.15s ease;
}

.drop:hover,
.drop.is-drag,
.drop.has-file {
  border-color: #7eae96;
  background: #f4faf7;
}

.drop.is-drag {
  transform: translateY(-1px);
}

.drop input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.drop-title {
  font-weight: 600;
  word-break: break-all;
}

.drop-hint {
  color: var(--muted);
  font-size: 13px;
}

.actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

button {
  appearance: none;
  border: 0;
  background: var(--accent);
  color: #f7fffb;
  font-size: 14px;
  font-weight: 600;
  padding: 11px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.15s ease;
}

button:hover:not(:disabled) {
  background: var(--accent-dark);
}

button:disabled {
  opacity: 0.42;
  cursor: not-allowed;
}

button:focus-visible,
.composer input:focus-visible {
  outline: 2px solid #b7dccb;
  outline-offset: 2px;
}

.composer {
  display: flex;
  gap: 8px;
}

.composer input {
  flex: 1;
  min-width: 0;
  border: 1px solid var(--line);
  background: #faf8f4;
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 15px;
  color: var(--ink);
}

.composer input:focus {
  outline: none;
  border-color: #7eae96;
  box-shadow: 0 0 0 3px rgba(31, 107, 74, 0.12);
}

.answer {
  margin-top: 16px;
  border-radius: 16px;
  background: #f7f5f0;
  padding: 16px 16px 14px;
  min-height: 108px;
}

.answer.is-error {
  background: #fdf2f1;
}

.answer-text {
  margin: 0;
  line-height: 1.75;
  white-space: pre-wrap;
}

.placeholder {
  margin: 8px 0 0;
  color: #8a837a;
  font-size: 14px;
}

.bar {
  display: block;
  height: 10px;
  width: 72%;
  border-radius: 999px;
  background: linear-gradient(90deg, #e7e2d8, #f6f3ec, #e7e2d8);
  background-size: 200% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
}

.bar.short {
  width: 42%;
  margin-top: 8px;
}

.sources {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 14px;
}

.source {
  font-size: 12px;
  line-height: 1.4;
  color: var(--accent-dark);
  background: #fff;
  border: 1px solid #d7e8df;
  border-radius: 999px;
  padding: 4px 9px;
}

.note {
  margin: 12px 0 0;
  font-size: 14px;
}

.note.is-ok {
  color: var(--accent-dark);
}

.note.is-error {
  color: var(--danger);
}

@keyframes shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}

@media (max-width: 640px) {
  .page {
    padding-top: 32px;
  }

  h1 {
    font-size: 28px;
  }

  .composer,
  .actions {
    flex-direction: column;
  }

  .actions button,
  .composer button {
    width: 100%;
  }
}
</style>
