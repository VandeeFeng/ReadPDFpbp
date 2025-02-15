Forked form <https://github.com/echohive42/AI-reads-books-page-by-page> , A  good start to build PDF studying system.

# PDF智能阅读助手 (ReadPDFpbp)

> 一个基于AI的PDF智能阅读和知识提取工具，帮助你更高效地学习和理解PDF文档。

## 🌟 特色功能

- 📚 自动分页处理PDF文档
- 🤖 智能识别和跳过无关内容（目录、参考文献等）
- 💡 自动提取关键知识点
- 📊 定期生成阶段性总结
- 📝 生成最终的综合分析报告
- 🌐 支持中文输出
- 🔄 断点续传功能（可从上次处理位置继续）
- 🧹 支持清理历史分析数据

## 📦 项目结构

```
ReadPDFpbp/
├── read_books.py      # 主程序文件
├── requirements.txt   # 依赖包列表
├── book_analysis/    # 分析结果存储目录
│   └── [书名]/
│       ├── pdfs/     # PDF文件存储
│       ├── knowledge_bases/  # 知识库JSON文件
│       └── summaries/  # 阶段性和最终总结
└── README.md         # 项目说明文档
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- OpenAI API 密钥或本地 Ollama 环境

### 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/VandeeFeng/ReadPDFpbp.git
cd ReadPDFpbp
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

### 使用方法

基本使用：
```bash
python read_books.py --pdf "your_book.pdf" --interval 10
```

参数说明：
- `--pdf`: PDF文件名（必需）
- `--interval`: 生成阶段性总结的页数间隔（默认5页）
- `--clean`: 清理已有的分析数据（可选）

## 🔧 配置选项

### 环境变量配置

根据选择的 API provider，需要设置相应的环境变量：

- OpenAI:
  ```bash
  export OPENAI_API_KEY=your_api_key_here
  ```

- OpenRouter:
  ```bash
  export OPENROUTER_API_KEY=your_api_key_here
  ```

- Ollama:
  无需设置环境变量，默认使用本地服务

### 命令行参数

在 `read_books.py` 中可以配置：
- `--pdf/-p`: PDF文件路径
- `--interval/-i`: 生成阶段性总结的页数间隔（默认5页）
- `--clean/-c`: 清理已有的分析数据
- `--provider/-P`: 选择 API provider（ollama/openai/openrouter）
- `--model/-m`: 使用的 AI 模型
- `--analysis-model/-am`: 用于分析的 AI 模型

示例：
```bash
# 使用 OpenAI
python read_books.py -p "book.pdf" -P openai

# 使用 OpenRouter
python read_books.py -p "book.pdf" -P openrouter

# 使用本地 Ollama（默认）
python read_books.py -p "book.pdf"
```

## 📝 输出说明

1. **知识库文件**：
   - 格式：JSON
   - 位置：`book_analysis/[书名]/knowledge_bases/`
   - 内容：包含提取的所有知识点

2. **阶段性总结**：
   - 格式：Markdown
   - 位置：`book_analysis/[书名]/summaries/[时间戳]/`
   - 内容：每N页的阶段性总结

3. **最终分析报告**：
   - 格式：Markdown
   - 位置：`book_analysis/[书名]/summaries/[时间戳]/`
   - 内容：整本书的综合分析


## 🙏 致谢

本项目基于 [AI-reads-books-page-by-page](https://github.com/echohive42/AI-reads-books-page-by-page) 改进开发。



