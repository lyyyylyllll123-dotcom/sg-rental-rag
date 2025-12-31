# Singapore Rental RAG Assistant

> 🏠 **Singapore Rental RAG Assistant** – 基于 LangChain 的本地知识库 RAG 系统，用于回答新加坡租房相关的资格、规则、流程、风险问题。

## 📋 项目简介

这是一个**信息整合与引用型问答系统**，专注于新加坡租房相关的官方信息：

- ✅ **不是聊天机器人** - 专注于结构化信息问答
- ✅ **不是法律咨询** - 仅提供信息整合与引用
- ✅ **不替代官方判断** - 重要决策请咨询官方机构

### 支持的问题类型

- ✅ 是否具备租房资格（Student Pass / EP / LTVP 等）
- ✅ HDB 与私人住宅的租赁规则差异
- ✅ 最短租期、人数限制、整套 vs 房间出租
- ✅ 租房流程（看房 → 合同 → 押金 → 入住）
- ✅ 官方风险提示与违规后果

### 明确不支持

- ❌ 房租价格预测
- ❌ 法律责任裁决
- ❌ 个案争议判断
- ❌ 非官方来源信息
- ❌ 承诺政策一定最新

## 🛠️ 技术栈

- **Python 3.10+**
- **LangChain** - 核心 RAG 框架
- **FAISS** - 向量数据库（本地持久化）
- **Streamlit** - Web UI
- **DeepSeek API** - LLM（OpenAI-compatible）
- **sentence-transformers** - 本地 Embedding 模型（语义检索）
- **CrossEncoder** - 重排序模型（`cross-encoder/ms-marco-MiniLM-L-6-v2`）
- **trafilatura / readability-lxml** - 网页正文抽取

## 📁 项目结构

```
RAG_/
├── app.py                    # Streamlit Web UI
├── ingest.py                  # 数据采集与入库
├── evaluate.py                # RAG 系统评测
├── config.py                  # 配置文件
├── requirements.txt           # 依赖包
├── data/
│   ├── urls.json             # URL 配置列表
│   ├── evaluation_questions.json  # 评测问题
│   └── faiss/                 # FAISS 向量库（持久化）
├── rag/
│   ├── retriever.py          # 检索器模块
│   ├── chain.py              # RAG 链模块
│   ├── prompt.py             # Prompt 模板
│   └── reranker.py           # 重排序模块
├── llm/
│   └── deepseek_llm.py        # DeepSeek LLM 封装
└── utils/
    ├── html_loader.py         # 网页加载器
    └── text_cleaner.py        # 文本清理工具
```

## 🔧 安装与配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

在 `config.py` 中已配置默认 API Key，或通过环境变量设置：

```bash
export OPENAI_API_KEY="your_deepseek_api_key"
export OPENAI_BASE_URL="https://api.deepseek.com/v1"
export MODEL_NAME="deepseek-chat"
```

### 3. 配置 URL 列表

编辑 `data/urls.json`，添加要采集的官方网页 URL（仅限白名单域名）：

- `gov.sg`
- `hdb.gov.sg`
- `cea.gov.sg`
- `ura.gov.sg`

## 📥 数据采集（Ingest）

### 运行数据采集

```bash
python ingest.py
```

### 采集流程

1. 从 `data/urls.json` 读取 URL 列表
2. 抓取网页并提取正文（使用 trafilatura / readability-lxml）
3. 生成 LangChain Document（包含 metadata: url, title, source, fetch_date）
4. 使用 `RecursiveCharacterTextSplitter` 切分文档
   - 默认 `chunk_size=500`, `chunk_overlap=100`
5. 生成 Embeddings（使用本地模型）
6. 写入 FAISS 向量库（持久化到 `./data/faiss`）

### 自定义参数

```bash
python ingest.py \
  --urls ./data/urls.json \
  --chunk-size 500 \
  --chunk-overlap 100 \
  --persist-dir ./data/faiss
```

### 规模控制

- 目标页面数：25-40 页
- 每页切分为 3-6 chunks
- 总 chunk 数目标：100-200
- 新页面若与已有内容高度重复（>80%），需停止采集

## 🚀 运行 Web UI

```bash
streamlit run app.py
```

### UI 功能

- 问题输入框
- 用户身份选择（Student Pass / EP / 不确定）
- 回答展示（Markdown 格式）
- 引用卡片（可点击 URL + 原文片段）
- "未找到资料"明确提示

### 回答风格

系统采用**三段自然语言结构**，不使用任何格式化标签（如"结论/说明/建议"等）。回答会：

- **第一段（1-2 句话）**：直接回答核心问题，给出当前情境下最关键、最有用的结论。使用"在大多数情况下/通常/实务中"等表述，避免绝对化。
- **第二段（简洁自然）**：解释「为什么是这个结论」，重点说明背后的核心规则或逻辑，不需要完整复述法律条文。
- **第三段（2-3 条建议）**：给出实际可执行的建议，聚焦"你接下来可以怎么做"，语气友好、实用。

回答风格专业、克制、有人情味，帮助用户理解"能不能做、为什么、接下来怎么看"。

### 重排序技术

系统使用**两阶段检索策略**提升回答质量：

1. **初始检索**：使用 FAISS 语义检索，检索 20 条候选文档
2. **重排序**：使用 CrossEncoder 对候选文档重新排序，选择最相关的 Top 8 条

**效果验证**：平均相关性提升 46.4%，Top-3 相关性提升 26.0%，100% 的评测问题都有改进。

## 📊 系统评测

### 运行评测

```bash
python evaluate.py
```

### 评测功能

- 批量运行评测问题（从 `data/evaluation_questions.json` 加载）
- 记录是否有引用
- 输出 Markdown 报告（`evaluation_report.md`）
- 展示失败样例（至少 5 条）

### 自定义评测

```bash
python evaluate.py \
  --questions ./data/evaluation_questions.json \
  --output ./evaluation_report.md
```

## 📚 数据来源

### 官方白名单域名

本系统**仅采集**以下官方/半官方域名的网页：

- ✅ `gov.sg` - 新加坡政府网站
- ✅ `hdb.gov.sg` - 建屋发展局
- ✅ `cea.gov.sg` - 房地产代理理事会
- ✅ `ura.gov.sg` - 市区重建局

### 禁止采集

- ❌ 全网爬虫
- ❌ 搜索 API
- ❌ 社交媒体
- ❌ 中介/商业博客
- ❌ 新闻网站

### 页面采集 Checklist

**HDB：**
- 租房资格（Who can rent / Eligibility）
- 最短租期（整套 vs 房间）
- 人数限制
- 公共租赁（PPH，如适用）

**gov.sg：**
- 出租流程总览
- 合规要求
- 常见违规与处罚

**CEA：**
- 租客视角租房步骤
- 合同注意事项
- 常见风险与纠纷求助入口

**URA：**
- 私人住宅租赁规则
- 私宅最短租期要求

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | DeepSeek API Key | `sk-4050f4f681bd46dbba956ce599b8dc1f` |
| `OPENAI_BASE_URL` | API Base URL | `https://api.deepseek.com/v1` |
| `MODEL_NAME` | 模型名称 | `deepseek-chat` |
| `EMBEDDING_MODEL` | Embedding 模型 | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| `CHUNK_SIZE` | 文档切分大小 | `500` |
| `CHUNK_OVERLAP` | 文档切分重叠 | `100` |
| `RETRIEVAL_K` | 检索文档数量 | `8` |

### config.py

所有配置集中在 `config.py` 中，支持环境变量覆盖。

## ⚠️ 已知限制与免责声明

### 已知限制

1. **数据时效性**：网页内容可能不是最新版本，政策可能已更新
2. **覆盖范围**：仅覆盖官方白名单域名的公开网页
3. **语言支持**：主要支持中文和英文问答
4. **检索精度**：依赖 Embedding 相似度，可能检索到不相关内容

### 免责声明

1. **非法律咨询**：本系统仅提供信息整合与引用，不构成法律咨询
2. **不保证最新**：所有信息来源于采集时的官方文档，不保证政策一定最新
3. **不替代官方判断**：重要决策（如租房合同、法律纠纷）请咨询官方机构
4. **信息准确性**：系统基于 RAG 技术，可能存在信息提取或理解偏差

**重要提示**：对于涉及法律、财务或重大决策的问题，请务必咨询：
- HDB（建屋发展局）
- CEA（房地产代理理事会）
- URA（市区重建局）
- 专业法律顾问

## 📝 开发说明

### RAG Pipeline 流程

1. 用户问题 → Embedding
2. Retriever 从 FAISS 检索 top_k（初始检索 20 条）
3. CrossEncoder 重排序，选择最相关的 Top 8 条文档
4. 将检索到的 Document 作为**唯一上下文**
5. 构建 RetrievalQA Chain：
   - Prompt 强制"只基于上下文回答"
   - 不允许外推
6. 输出自然语言三段式回答 + 引用

### 关键设计原则

- **LLM 仅用于总结与重述**：不允许使用常识补充或外部知识
- **检索不到就明确说明**："资料库未覆盖该问题"
- **所有信息必须来自上下文**：Prompt 中明确禁止外推

## 📄 License

MIT License

---

**Made with ❤️ for Singapore rental information seekers**







