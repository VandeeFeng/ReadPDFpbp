from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel
import json
from openai import OpenAI
import fitz  # PyMuPDF
from termcolor import colored
from datetime import datetime
import shutil
import argparse
import os

# need to solve the openAI client problem,because i used openrouter

# 设置命令行参数解析器
def parse_args():
    parser = argparse.ArgumentParser(description="Process PDF analysis.")
    parser.add_argument(
        '-p', '--pdf',
        type=str,
        required=True,
        help="The name of the PDF file"
    )
    parser.add_argument(
        '-i', '--interval',
        type=int,
        default=5,
        help="The interval for analysis (set to None to skip)"
    )
    parser.add_argument(
        '-c', '--clean',
        nargs='?',
        const='all',
        choices=['all', 'k', 's'],
        help="Clean options: no value or 'all' for everything, 'k' for knowledge base, 's' for summaries"
    )
    return parser.parse_args()

# 检查 pdf_name 参数
def validate_pdf_name(pdf_name):
    # 确保文件名符合规范并且有 .pdf 扩展名
    if not pdf_name.endswith(".pdf"):
        print(f"Error: The file '{pdf_name}' does not have a valid PDF extension. Please provide a valid PDF file.")
        exit(1)

    # 检查文件是否存在
    if not os.path.isfile(pdf_name):
        print(f"Error: The file '{pdf_name}' does not exist. Please provide a valid file path.")
        exit(1)

# 解析命令行参数
args = parse_args()

# 使用命令行传入的参数
PDF_NAME = args.pdf
ANALYSIS_INTERVAL = args.interval

# Configuration Constants
# PDF_NAME = "UnderstandingDeepLearning_07_02_24_C.pdf"
BASE_DIR = Path("book_analysis") / Path(PDF_NAME).stem
PDF_DIR = BASE_DIR / "pdfs"
KNOWLEDGE_DIR = BASE_DIR / "knowledge_bases"
SUMMARIES_DIR = BASE_DIR / "summaries"
PDF_PATH = PDF_DIR / PDF_NAME
OUTPUT_PATH = KNOWLEDGE_DIR / f"{PDF_NAME.replace('.pdf', '_knowledge.json')}"
# ANALYSIS_INTERVAL = 20  # Set to None to skip interval analyses, or a number (e.g., 10) to generate analysis every N pages
MODEL = "qwen2.5:14b"
ANALYSIS_MODEL = "qwen2.5:14b"
TEST_PAGES = None  # Set to None to process entire book


class PageContent(BaseModel):
    has_content: bool
    knowledge: list[str]


def load_or_create_knowledge_base() -> Dict[str, Any]:
    if Path(OUTPUT_PATH).exists():
        with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_knowledge_base(knowledge_base: list[str]):
    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    output_path = KNOWLEDGE_DIR / f"{PDF_NAME.replace('.pdf', '')}_knowledge.json"
    print(colored(f"💾 Saving knowledge base ({len(knowledge_base)} items)...", "blue"))
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({"knowledge": knowledge_base}, f, indent=2, ensure_ascii=False)

def process_page(client: OpenAI, page_text: str, current_knowledge: list[str], page_num: int) -> list[str]:
    print(colored(f"\n📖 Processing page {page_num + 1}...", "yellow"))

    completion = client.beta.chat.completions.parse(
        model=ANALYSIS_MODEL,
        messages=[
            {"role": "system", "content": """Analyze this page as if you're studying from a book. and all your answers must in chinese.

            SKIP content if the page contains:
            - Table of contents
            - Chapter listings
            - Index pages
            - Blank pages
            - Copyright information
            - Publishing details
            - References or bibliography
            - Acknowledgments

            DO extract knowledge if the page contains:
            - Preface content that explains important concepts
            - Actual educational content
            - Key definitions and concepts
            - Important arguments or theories
            - Examples and case studies
            - Significant findings or conclusions
            - Methodologies or frameworks
            - Critical analyses or interpretations

            For valid content:
            - Set has_content to true
            - Extract detailed, learnable knowledge points
            - Include important quotes or key statements
            - Capture examples with their context
            - Preserve technical terms and definitions

            For pages to skip:
            - Set has_content to false
            - Return empty knowledge list"""},
            {"role": "user", "content": f"Page text: {page_text}"}
        ],
        response_format=PageContent
    )

    result = completion.choices[0].message.parsed
    if result.has_content:
        print(colored(f"✅ Found {len(result.knowledge)} new knowledge points", "green"))
    else:
        print(colored("⏭️  Skipping page (no relevant content)", "yellow"))

    updated_knowledge = current_knowledge + (result.knowledge if result.has_content else [])

    # Update single knowledge base file
    save_knowledge_base(updated_knowledge)

    return updated_knowledge

def load_existing_knowledge() -> list[str]:
    knowledge_file = KNOWLEDGE_DIR / f"{PDF_NAME.replace('.pdf', '')}_knowledge.json"
    if knowledge_file.exists():
        print(colored("📚 Loading existing knowledge base...", "cyan"))
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(colored(f"✅ Loaded {len(data['knowledge'])} existing knowledge points", "green"))
            return data['knowledge']
    print(colored("🆕 Starting with fresh knowledge base", "cyan"))
    return []

def analyze_knowledge_base(client: OpenAI, knowledge_base: list[str], start_page: int = None, end_page: int = None) -> str:
    if not knowledge_base:
        print(colored("\n⚠️  Skipping analysis: No knowledge points collected", "yellow"))
        return ""

    print(colored("\n🤔 Generating final book analysis...", "cyan"))
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": """Create a comprehensive summary of the provided content in a concise but detailed way, Explain the concepts of professional terminology，using markdown format.and all your answers must in chinese.

            Use markdown formatting:
            - ## for main sections
            - ### for subsections
            - Bullet points for lists
            - `code blocks` for any code or formulas
            - **bold** for emphasis
            - *italic* for terminology
            - > blockquotes for important notes

            Return only the markdown summary, nothing else. Do not say 'here is the summary' or anything like that before or after"""},
            {"role": "user", "content": f"Analyze this content:\n" + "\n".join(knowledge_base)}
        ]
    )

    print(colored("✨ Analysis generated successfully!", "green"))
    return completion.choices[0].message.content

def setup_directories():

    # Create all necessary directories
    for directory in [PDF_DIR, KNOWLEDGE_DIR, SUMMARIES_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    # Ensure PDF exists in correct location
    if not PDF_PATH.exists():
        source_pdf = Path(PDF_NAME)
        if source_pdf.exists():
            # Copy the PDF instead of moving it
            shutil.copy2(source_pdf, PDF_PATH)
            print(colored(f"📄 Copied PDF to analysis directory: {PDF_PATH}", "green"))
        else:
            raise FileNotFoundError(f"PDF file {PDF_NAME} not found")

def save_summary(summary: str, is_final: bool = False, output_dir: Path = None, start_page: int = None, end_page: int = None):
    if not summary:
        print(colored("⏭️  Skipping summary save: No content to save", "yellow"))
        return

    # Create markdown file with proper naming
    if is_final:
        existing_summaries = list(output_dir.glob(f"{PDF_NAME.replace('.pdf', '')}_final_*.md"))
        next_number = len(existing_summaries) + 1
        summary_path = output_dir / f"{PDF_NAME.replace('.pdf', '')}_final_{next_number:03d}.md"
    else:
        existing_summaries = list(output_dir.glob(f"{PDF_NAME.replace('.pdf', '')}_interval_*.md"))
        next_number = len(existing_summaries) + 1
        summary_path = output_dir / f"{PDF_NAME.replace('.pdf', '')}_interval_{next_number:03d}.md"

    # 构建页码范围信息
    page_range = ""
    if start_page is not None:
        if end_page is None or start_page == end_page:
            page_range = f"\n📖 分析范围：第 {start_page} 页\n\n"
        else:
            page_range = f"\n📖 分析范围：第 {start_page} - {end_page} 页\n\n"

    # Create markdown content with metadata
    markdown_content = f"""# Book Analysis: {PDF_NAME}
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}{page_range}
{summary}

---
*Analysis generated using AI Book Analysis Tool*
"""

    print(colored(f"\n📝 Saving {'final' if is_final else 'interval'} analysis to markdown...", "cyan"))
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    print(colored(f"✅ Analysis saved to: {summary_path}", "green"))

def print_instructions():
    print(colored("""
📚 PDF Book Analysis Tool 📚
---------------------------
1. Place your PDF in the same directory as this script
2. Update PDF_NAME constant with your PDF filename
3. The script will:
   - Process the book page by page
   - Extract and save knowledge points
   - Generate interval summaries (if enabled)
   - Create a final comprehensive analysis

Configuration options:
- ANALYSIS_INTERVAL: Set to None to skip interval analyses, or a number for analysis every N pages
- TEST_PAGES: Set to None to process entire book, or a number for partial processing

type --pdf "name.pdf" and --interval 10

Press Enter to continue or Ctrl+C to exit...
""", "cyan"))

# 清理函数
def clean_directories():
    print(colored("\n🧹 Starting cleanup...", "yellow"))
    
    # 根据参数决定清理范围
    if args.clean in ['all', 's']:
        if SUMMARIES_DIR.exists():
            for file in SUMMARIES_DIR.glob("**/*"):
                if file.is_file():
                    file.unlink()
                elif file.is_dir() and not any(file.iterdir()):
                    file.rmdir()
            print(colored("✨ Summaries directory cleaned", "green"))
        else:
            print(colored("📂 No summaries directory to clean", "yellow"))
    
    if args.clean in ['all', 'k']:
        if KNOWLEDGE_DIR.exists():
            for file in KNOWLEDGE_DIR.glob("*.json"):
                file.unlink()
            print(colored("✨ Knowledge base files cleaned", "green"))
        else:
            print(colored("📂 No knowledge base directory to clean", "yellow"))

def main():
    try:
        print_instructions()
        input()
    except KeyboardInterrupt:
        print(colored("\n❌ Process cancelled by user", "red"))
        return

    # 如果指定了 clean 参数，先清理目录
    if args.clean:
        clean_directories()

    setup_directories()

    # 创建本次运行的时间戳目录
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    current_run_dir = SUMMARIES_DIR / timestamp
    current_run_dir.mkdir(parents=True, exist_ok=True)

    '''
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="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",
    )
    '''
    client = OpenAI(
        base_url='http://localhost:11434/v1/',
        api_key='ollama',
    )
     # Load or initialize knowledge base
    knowledge_base = load_existing_knowledge()

    pdf_document = fitz.open(PDF_PATH)
    pages_to_process = TEST_PAGES if TEST_PAGES is not None else pdf_document.page_count

    print(colored(f"\n📚 Processing {pages_to_process} pages...", "cyan"))
    for page_num in range(min(pages_to_process, pdf_document.page_count)):
        page = pdf_document[page_num]
        page_text = page.get_text()

        knowledge_base = process_page(client, page_text, knowledge_base, page_num)

        # Generate interval analysis if ANALYSIS_INTERVAL is set
        if ANALYSIS_INTERVAL:
            is_interval = (page_num + 1) % ANALYSIS_INTERVAL == 0
            is_final_page = page_num + 1 == pages_to_process

            if is_interval and not is_final_page:
                print(colored(f"\n📊 Progress: {page_num + 1}/{pages_to_process} pages processed", "cyan"))
                interval_start = max(1, page_num - ANALYSIS_INTERVAL + 2)
                interval_summary = analyze_knowledge_base(client, knowledge_base, start_page=interval_start, end_page=page_num + 1)
                save_summary(interval_summary, is_final=False, output_dir=current_run_dir,
                           start_page=interval_start, end_page=page_num + 1)

        # Always generate final analysis on last page
        if page_num + 1 == pages_to_process:
            print(colored(f"\n📊 Final page ({page_num + 1}/{pages_to_process}) processed", "cyan"))
            final_summary = analyze_knowledge_base(client, knowledge_base, start_page=1, end_page=page_num + 1)
            save_summary(final_summary, is_final=True, output_dir=current_run_dir,
                        start_page=1, end_page=page_num + 1)

    print(colored("\n✨ Processing complete! ✨", "green", attrs=['bold']))

if __name__ == "__main__":
    main()
