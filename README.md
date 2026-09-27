# kbqa-rag · 知识库智能问答

基于 RAG 的个人知识库问答。上传 PDF 后用自然语言提问，回答只依据文档内容，并标出来源；资料里没有的内容会明确说明无法回答。
从零实现 RAG 全链路：FastAPI + Chroma + bge-m3 + DeepSeek，PDF 语义检索问答，支持来源溯源。

## 技术栈

- 后端：Python 3.12、FastAPI、Uvicorn
- 检索：pypdf 解析 PDF，LangChain 按约 500 字切块（重叠 50 字），硅基流动上的 bge-m3 向量化，Chroma 持久化并取最相关的 3 块
- 生成：DeepSeek `deepseek-chat`
- 前端：Vue 3、TypeScript、Vite

## 环境准备

需要 Python 3.12、Node.js，以及两个 API Key：

- [DeepSeek](https://platform.deepseek.com/)：对话生成
- [硅基流动](https://cloud.siliconflow.cn/)：bge-m3 向量化

在项目根目录复制环境变量模板并填入自己的 Key：

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

```env
DEEPSEEK_API_KEY=your_api_key_here
SILICONFLOW_API_KEY=your_api_key_here
```

`.env`、本地向量库 `chroma_db/` 和 `docs/` 里的文档不会提交到仓库。

## 本地运行

开两个终端。

```bash
# 后端，http://127.0.0.1:8000
pip install -r requirements.txt
uvicorn app:app --reload
```

```bash
# 前端，http://127.0.0.1:5173
cd frontend
npm install
npm run dev
```

页面上选择或拖入 PDF，解析入库后再提问。前端请求写死为 `http://127.0.0.1:8000`，后端和页面需要在本机同时运行。

扫描版 PDF 没有文字层，解析后不会产生文本块。

## 其他用法

网页上传之外，也可以把文档放到 `docs/` 后一次性入库。支持 `.pdf`、`.txt`、`.md`。目录里至少放一份文档再运行，脚本会清空已有的 `knowledge` 集合后重新写入：

```bash
python ingest.py
```

入库后可以用命令行提问，输入 `q` 退出：

```bash
python qa.py
```

## 接口

`POST /upload`：表单字段 `file`，上传一份 PDF。返回文件名和切出的文本块数量。同名文件再次上传会覆盖之前的块。

`GET /ask?question=...`：返回答案和来源文件名。

```json
{
  "answer": "……",
  "sources": ["笔记.pdf"]
}
```

## Docker

镜像只包含后端 API，不包含前端页面。构建文件名是小写的 `dockerfile`：

```bash
docker build -f dockerfile -t kbqa-rag .
docker run -p 8000:8000 --env-file .env kbqa-rag
```

容器起来后访问 `http://127.0.0.1:8000/docs` 调试接口。向量库在容器内，删除容器后需要重新上传文档。

## 项目结构

```text
app.py                 网页使用的 FastAPI 服务
ingest.py              将 docs/ 批量入库
qa.py                  命令行问答
frontend/              Vue 页面
docs/                  批量入库目录，内容不提交
dockerfile             后端镜像
embedding_demo.py      向量相似度示例
chroma_demo.py         Chroma 检索示例
hello.py               DeepSeek 调用示例
main.py                早期多轮对话接口，不含文档检索
```

## 许可证

[MIT](LICENSE)
