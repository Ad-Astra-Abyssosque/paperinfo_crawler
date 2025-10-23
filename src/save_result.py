import json
import os.path

import bibtexparser

from data import PaperInfo
import logging

logger = logging.getLogger()


def save_result(file_path: str, papers: list[PaperInfo], detailed: bool = False):
    dir = os.path.dirname(file_path)
    if not os.path.exists(dir):
        os.makedirs(dir, exist_ok=True)

    if file_path.endswith(".md"):
        save_as_markdown(file_path, papers)
    elif file_path.endswith(".json"):
        save_as_json(file_path, papers, detailed)
    elif file_path.endswith(".bib"):
        save_as_bibtex(file_path, papers, detailed)
    elif file_path.endswith(".csv"):
        save_as_csv(file_path, papers, detailed)
    else:
        logger.error(f"Unsupported format: {os.path.basename(file_path)}")


def save_as_markdown(file_path: str, papers: list[PaperInfo]):
    """将论文信息列表以 Markdown 格式追加写入文件。"""
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            for paper in papers:
                f.write(f"### {paper.title}\n")
                f.write(f"**URL**: {paper.url}\n")
                f.write("**Abstract**:\n")
                f.write(f"{paper.abstract.strip()}\n\n")
                # 每个条目之间空一行
                f.write("\n")
        logger.info(f"成功写入 {len(papers)} 篇论文到 {file_path}")
    except Exception as e:
        logger.error(f"写入 Markdown 文件失败: {e}")
        raise


def save_as_json(file_path: str, papers: list[PaperInfo], detailed: bool = False):
    """将论文信息列表保存为 JSON 文件。

    Args:
        file_path (str): 保存路径
        papers (list[PaperInfo]): PaperInfo 对象列表
        detailed (bool): 若为 True，则解析 bibtex 字段并写入详细信息
    """
    # 1. 尝试读取旧数据
    existing_data = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    existing_data = json.loads(content)
                    if not isinstance(existing_data, list):
                        logger.warning(f"{file_path} 格式异常，非列表结构，将覆盖写入。")
                        existing_data = []
        except Exception as e:
            logger.warning(f"读取旧 JSON 文件失败，将新建: {e}")
            existing_data = []

    # 2. 组装新论文数据
    new_entries = []
    for paper in papers:
        entry = {
            "title": paper.title,
            "url": paper.url,
            "abstract": paper.abstract.strip(),
        }

        # 如果 detailed=True 且存在 bibtex，则解析附加字段
        if detailed and paper.bibtex:
            try:
                bib_db = bibtexparser.parse_string(paper.bibtex)
                if bib_db.entries:
                    bib_entry = bib_db.entries[0]
                    for key, val in bib_entry.items():
                        if key not in entry:
                            entry[key] = val
            except Exception as e:
                logger.warning(f"解析 bibtex 失败（{paper.title}）: {e}")

        new_entries.append(entry)

    # 3. 合并并写入文件
    combined = existing_data + new_entries
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(combined, f, ensure_ascii=False, indent=4)
        if existing_data:
            logger.info(f"已向 {file_path} 追加 {len(new_entries)} 篇论文（共 {len(combined)} 篇）")
        else:
            logger.info(f"已创建新文件 {file_path} 并写入 {len(new_entries)} 篇论文")
    except Exception as e:
        logger.error(f"写入 JSON 文件失败: {e}")
        raise


def save_as_bibtex(file_path: str, papers: list[PaperInfo], detailed: bool = False):
    pass


def save_as_csv(file_path: str, papers: list[PaperInfo], detailed: bool = False):
    pass


def get_result_num(file_path: str):
    if file_path.endswith(".md"):
        return read_markdown_results_num(file_path)
    elif file_path.endswith(".json"):
        return read_json_results_num(file_path)
    elif file_path.endswith(".bib"):
        return read_bibtex_results_num(file_path)
    elif file_path.endswith(".csv"):
        return read_csv_results_num(file_path)
    else:
        logger.error(f"Unsupported format: {os.path.basename(file_path)}")
        return 0


def read_json_results_num(file_path: str) -> int:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                existing_data = json.loads(content)
                return len(existing_data)
    return 0


def read_markdown_results_num(file_path: str) -> int:
    return 0


def read_csv_results_num(file_path: str) -> int:
    return 0


def read_bibtex_results_num(file_path: str) -> int:
    return 0
