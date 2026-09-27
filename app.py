import io
import os
import chromadb
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI

load_dotenv()

embed_client = OpenAI(
    api_key=os.getenv("SILICONFLOW_API_KEY"),
    base_url="https://api.siliconflow.cn/v1",
)
chat_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="knowledge")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
)

app = FastAPI(title="kbqa-rag")

# 允许前端跨域访问（你 React 跑在别的端口，必须开）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def embed(texts):
    resp = embed_client.embeddings.create(model="BAAI/bge-m3", input=texts)
    return [d.embedding for d in resp.data]

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    # 读取上传的 PDF 并解析
    content = await file.read()
    reader = PdfReader(io.BytesIO(content))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    chunks = splitter.split_text(text)

    # 用文件名作为这批块的 id 前缀，避免重复上传冲突
    prefix = file.filename.replace(".pdf", "").replace(" ", "_")
    existing = [i for i in collection.get()["ids"] if i.startswith(prefix)]
    if existing:  # Chroma 不允许 delete([])，首次上传库里没有同前缀 id
        collection.delete(existing)

    BATCH = 16
    for i in range(0, len(chunks), BATCH):
        batch = chunks[i:i+BATCH]
        collection.add(
            ids=[f"{prefix}_{j}" for j in range(i, i+len(batch))],
            documents=batch,
            embeddings=embed(batch),
            metadatas=[{"source": file.filename}] * len(batch),
        )
    return {"filename": file.filename, "chunks": len(chunks)}

@app.get("/ask")
def ask(question: str):
    q_emb = embed([question])[0]
    result = collection.query(query_embeddings=[q_emb], n_results=3)
    contexts = result["documents"][0]
    sources = sorted({m["source"] for m in result["metadatas"][0]})

    prompt = f"""请严格根据下面提供的参考资料回答用户问题。
如果资料中没有相关内容，就直接说"根据现有资料无法回答"，不要自己编造。
回答简洁准确。

参考资料：
{chr(10).join(contexts)}

用户问题：{question}"""

    response = chat_client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
    )
    return {"answer": response.choices[0].message.content, "sources": sources}