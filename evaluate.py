"""
RAG 系统评测模块
批量运行评测问题，生成评测报告
"""
import json
import os
from typing import List, Dict, Any
from datetime import datetime

from llm.deepseek_llm import get_deepseek_llm
from rag.retriever import load_vectorstore, create_retriever
from rag.chain import run_rag_query
from config import (
    FAISS_PERSIST_DIR,
    FAISS_INDEX_NAME,
    INITIAL_RETRIEVAL_K,
    EVALUATION_QUESTIONS_PATH,
)


def load_evaluation_questions(json_path: str = None) -> List[Dict[str, Any]]:
    """
    加载评测问题
    
    Args:
        json_path: 评测问题 JSON 文件路径
    
    Returns:
        评测问题列表
    """
    if json_path is None:
        json_path = EVALUATION_QUESTIONS_PATH
    
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"评测问题文件不存在: {json_path}")
    
    with open(json_path, "r", encoding="utf-8") as f:
        questions = json.load(f)
    
    return questions


def evaluate_rag_system(
    questions: List[Dict[str, Any]] = None,
    output_report: str = "./evaluation_report.md",
) -> Dict[str, Any]:
    """
    评测 RAG 系统
    
    Args:
        questions: 评测问题列表（如果为 None，从文件加载）
        output_report: 输出报告文件路径
    
    Returns:
        评测结果字典
    """
    # 加载评测问题
    if questions is None:
        questions = load_evaluation_questions()
    
    print(f"📋 加载了 {len(questions)} 个评测问题")
    
    # 检查向量库是否存在
    vectorstore = load_vectorstore(
        persist_directory=FAISS_PERSIST_DIR,
        index_name=FAISS_INDEX_NAME,
    )
    
    if vectorstore is None:
        raise ValueError(
            f"向量库不存在。请先运行 python ingest.py 进行数据采集。"
        )
    
    print(f"✅ 向量库加载成功")
    
    # 创建 LLM 和 Retriever
    try:
        llm = get_deepseek_llm()
        print(f"✅ LLM 初始化成功")
    except Exception as e:
        raise ValueError(f"LLM 初始化失败: {e}")
    
    # 使用初始检索数量（重排序会在 chain 内部处理）
    retriever = create_retriever(vectorstore, k=INITIAL_RETRIEVAL_K)
    print(f"✅ Retriever 创建成功 (初始检索 k={INITIAL_RETRIEVAL_K}，重排序后返回 8 条)")
    
    # 执行评测
    results = []
    success_count = 0
    no_citation_count = 0
    
    print(f"\n🚀 开始评测...\n")
    
    for i, q_config in enumerate(questions, 1):
        question = q_config.get("question", "")
        category = q_config.get("category", "unknown")
        
        print(f"[{i}/{len(questions)}] {question}")
        
        try:
            # 运行 RAG 查询
            result = run_rag_query(question, llm, retriever)
            
            answer = result.get("answer", "")
            citations = result.get("citations", [])
            
            # 判断是否有引用
            has_citations = len(citations) > 0
            
            # 判断是否成功（有引用且回答不为空）
            is_success = has_citations and len(answer.strip()) > 0
            
            if is_success:
                success_count += 1
            if not has_citations:
                no_citation_count += 1
            
            results.append({
                "question": question,
                "category": category,
                "answer": answer,
                "citations": citations,
                "has_citations": has_citations,
                "is_success": is_success,
            })
            
            status = "✅" if is_success else "⚠️"
            citation_status = f"引用: {len(citations)}" if has_citations else "无引用"
            print(f"   {status} {citation_status}")
            
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            results.append({
                "question": question,
                "category": category,
                "answer": "",
                "citations": [],
                "has_citations": False,
                "is_success": False,
                "error": str(e),
            })
    
    # 生成报告
    success_rate = (success_count / len(questions)) * 100 if questions else 0
    citation_rate = ((len(questions) - no_citation_count) / len(questions)) * 100 if questions else 0
    
    # 找出失败样例（至少 5 条，或所有失败的）
    failed_results = [r for r in results if not r.get("is_success", False)]
    failed_samples = failed_results[:max(5, len(failed_results))]
    
    # 生成 Markdown 报告
    report_lines = [
        "# RAG 系统评测报告",
        "",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 总体统计",
        "",
        f"- **总问题数**: {len(questions)}",
        f"- **成功回答**: {success_count} ({success_rate:.1f}%)",
        f"- **有引用**: {len(questions) - no_citation_count} ({citation_rate:.1f}%)",
        f"- **无引用**: {no_citation_count}",
        "",
        "## 失败样例",
        "",
    ]
    
    if failed_samples:
        for i, result in enumerate(failed_samples, 1):
            report_lines.extend([
                f"### 失败样例 {i}",
                "",
                f"**问题**: {result['question']}",
                f"**分类**: {result.get('category', 'unknown')}",
                f"**是否有引用**: {'是' if result.get('has_citations') else '否'}",
                "",
            ])
            
            if result.get("error"):
                report_lines.append(f"**错误**: {result['error']}")
            else:
                answer = result.get("answer", "")
                if answer:
                    report_lines.append(f"**回答**: {answer[:200]}...")
                else:
                    report_lines.append("**回答**: (空)")
            
            report_lines.append("")
    else:
        report_lines.append("无失败样例。")
        report_lines.append("")
    
    # 详细结果
    report_lines.extend([
        "## 详细结果",
        "",
        "| # | 问题 | 分类 | 有引用 | 成功 |",
        "|---|------|------|--------|------|",
    ])
    
    for i, result in enumerate(results, 1):
        question_short = result["question"][:50] + "..." if len(result["question"]) > 50 else result["question"]
        has_cit = "✅" if result.get("has_citations") else "❌"
        is_success = "✅" if result.get("is_success") else "❌"
        report_lines.append(
            f"| {i} | {question_short} | {result.get('category', 'unknown')} | {has_cit} | {is_success} |"
        )
    
    report_content = "\n".join(report_lines)
    
    # 保存报告
    with open(output_report, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"\n📊 评测完成:")
    print(f"   - 成功率: {success_rate:.1f}%")
    print(f"   - 引用率: {citation_rate:.1f}%")
    print(f"   - 失败样例: {len(failed_samples)} 个")
    print(f"   - 报告已保存: {output_report}")
    
    return {
        "total": len(questions),
        "success_count": success_count,
        "success_rate": success_rate,
        "citation_count": len(questions) - no_citation_count,
        "citation_rate": citation_rate,
        "failed_samples": failed_samples,
        "results": results,
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG 系统评测")
    parser.add_argument(
        "--questions",
        type=str,
        default=None,
        help="评测问题 JSON 文件路径",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./evaluation_report.md",
        help="输出报告文件路径",
    )
    
    args = parser.parse_args()
    
    # 执行评测
    evaluate_rag_system(
        questions=None if args.questions is None else load_evaluation_questions(args.questions),
        output_report=args.output,
    )

