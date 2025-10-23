import hashlib
import json
import logging
import os
import time
from time import sleep

import bs4
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from request_wrap import make_request
from settings import dblp_url
from data import PaperInfo
import utils

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
# handler = logging.StreamHandler()
# handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# handler.setFormatter(formatter)
# logger.addHandler(handler)


def get_conf_url(name: str, year: str) -> tuple[str, str]:
    """get URL of dblp.

    Args:
        namne (str): conference name
        year (str): conference year

    Returns:
        str: dblp URL
    """
    # 有时会议论文集收录在期刊中
    entry_type_in_url = "conf"

    # isdigit() is still unsafe here as it does not equal to test whether string is an integer
    if name == "csfw" and year.isdigit() and int(year) >= 2023:
        # csfw 2023和后续的会议URL特殊：csfw/csf[year].html
        conf_url = "{}conf/{}/{}{}.html".format(dblp_url, name, name[:-1], year)
    elif name == "conext" and year.isdigit() and int(year) >= 2023:
        # conext 从2023之后，长文收录在期刊 The Proceedings of the ACM on Networking (PAMCNET) journal
        conf_url = "{}journals/pacmnet/pacmnet{}.html".format(
            dblp_url, int(year) - 2022
        )
        entry_type_in_url = "journal"
    elif name == "kdd" and year == "2025":
        # kdd/kdd2025-1.html
        conf_url = "{}conf/{}/{}{}-1.html".format(dblp_url, name, name, year)
    elif name == "sigmod" and year.isdigit() and int(year) >= 2023:
        conf_url = "{}journals/pacmmod/pacmmod{}.html".format(
            dblp_url, int(year) - 2022
        )
        entry_type_in_url = "journal"
    else:
        conf_url = "{}conf/{}/{}{}.html".format(dblp_url, name, name, year)

    logger.debug(f"Type: {entry_type_in_url}, Request URL: {conf_url}")

    return conf_url, entry_type_in_url


def get_journal_url(name: str, volume: str) -> str:
    journal_url = "{}journals/{}/{}{}.html".format(dblp_url, name, name, volume)

    logger.debug("Request URL: {}".format(journal_url))

    return journal_url


def get_paper_title_and_url(entry: bs4.element.Tag) -> PaperInfo:
    """获取一篇论文的标题和URL

    Args:
        entry (bs4.element.Tag): 一篇论文经bs4解析后的HTML代码片段

    Returns:
        list: (论文标题，论文URL)
    """
    paper_title = None
    title_span_tag = entry.select_one(
        'cite.data.tts-content > span.title[itemprop="name"]'
    )
    if title_span_tag is not None:
        # 去除可能存在的空格和英文句号
        paper_title = title_span_tag.get_text().strip()[:-1]

    paper_url = None
    # 找到第一个a标签
    a_tag = entry.select_one("li.ee > a")
    if a_tag is not None:
        paper_url = a_tag["href"]
        # 只留下 doi.org 类型的 URL
        # doi.ieeecomputersociety.org 等URL无法访问，需要排除
        # e.g. "Space Odyssey: An Experimental Software Security Analysis of Satellites" in https://dblp.org/db/conf/sp/sp2023.html
        if "doi.ieeecomputersociety.org" in paper_url:
            logger.warning(
                "Unsupported URL {} of paper {}.".format(paper_url, paper_title)
            )
            paper_url = ""

    return PaperInfo(title=paper_title, url=paper_url)


def get_paper_bibtex(
    bibtex_session: requests.Session, entry: bs4.element.Tag, req_itv: float
) -> str | None:
    """获取bibtex格式的论文元数据

    Args:
        bibtex_session (requests.Session): 复用会话，建立连接
        entry (bs4.element.Tag): 一篇论文经bs4解析后的的HTML代码片段
        req_itv (float): bibtex请求之间的时间间隔（秒）。

    Returns:
        str: bibtex字符串
    """
    bibtex_url = None
    bibtex_url_tag = entry.select_one(
        'li.drop-down > div.body > ul > li > a[rel="nofollow"]'
    )
    if bibtex_url_tag is not None:
        bibtex_url = bibtex_url_tag["href"]
    else:
        logger.error("Cannot obtain bibtex URL.")
        return None

    if bibtex_url is not None:
        sleep(req_itv)
        bibtex_res = make_request(bibtex_session, str(bibtex_url))
        if bibtex_res is None:
            return None

        bibtex_soup = BeautifulSoup(bibtex_res.text, "html.parser")
        bibtex_content_tag = bibtex_soup.select_one(
            'div.section[id="bibtex-section"] > pre.verbatim.select-on-click'
        )
        if bibtex_content_tag is not None:
            bibtex_str = bibtex_content_tag.get_text()
            return bibtex_str
    # TODO 错误处理
    logger.error("Cannot obtain bibtex content.")
    return None


def get_cache_path(url: str) -> str:
    """根据URL生成唯一缓存文件路径"""
    cache_dir = os.path.join(os.path.dirname(__file__), '..', 'dblp_cache')
    os.makedirs(cache_dir, exist_ok=True)
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    return os.path.join(cache_dir, f'{url_hash}.json')


def load_cache(cache_path: str) -> list[PaperInfo]:
    """从缓存中读取已爬取的论文信息"""
    if not os.path.exists(cache_path):
        return []
    with open(cache_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [PaperInfo(d['title'], d['url'], d['bibtex']) for d in data]


def save_cache(cache_path: str, papers: list[PaperInfo]):
    """将已爬取信息写入缓存"""
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(
            [{'title': p.title, 'url': p.url, 'bibtex': p.bibtex} for p in papers],
            f,
            ensure_ascii=False,
            indent=2
        )


def get_dblp_page_content(url: str, req_itv: float, type: str, existed_num: int, count: int = 1) -> list[PaperInfo]:
    """获取页面中的论文网址

    Args:
        url (str): 期刊/会议某一期/某一年的URL。e.g. https://dblp.org/db/conf/sp/sp2023.html
        req_itv (float): bibtex请求之间的时间间隔（秒）。
        type (str): 爬取的论文类型。会议或期刊，"conf" or "journal"。
        existed_num: 已经爬取的论文数量
        count: 还需要爬取的论文数量

    Returns:
        list: PaperInfo[论文标题, 每篇论文的 doi.org URL, 不含摘要的bibtex字符串]。e.g. [WeRLman: To Tackle Whale (Transactions), Go Deep (RL), https://doi.org/10.1109/SP46215.2023.10179444, @inproceedings...]
    """
    res = requests.get(url)
    if res.status_code != 200:
        logger.error(f"{url} cannot be loaded. Make sure your input is valid.")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    if type == "conf":
        paper_entries = soup.select('li.entry.inproceedings[itemscope][itemtype="http://schema.org/ScholarlyArticle"]')
    elif type == "journal":
        paper_entries = soup.select('li.entry.article[itemscope][itemtype="http://schema.org/ScholarlyArticle"]')
    else:
        logger.error('Invalid type param. Should be "conf" or "journal"')
        return []

    target_idx = len(paper_entries) if count == -1 or count >= len(paper_entries) else count + existed_num
    logger.info(f"Total {len(paper_entries)} papers, collect {existed_num+1}-{target_idx} of them")

    # 加载缓存
    cache_path = get_cache_path(url)
    cached_papers = load_cache(cache_path)
    logger.info(f"Loaded {len(cached_papers)} cached papers from {cache_path}")

    entry_metadata_list = cached_papers.copy()
    bibtex_session = requests.Session()

    # 跳过已缓存部分
    start_idx = len(cached_papers)
    if start_idx < target_idx:
        logger.info(f"Start fetching DBLP entries from {start_idx} to {target_idx}")
    try:
        for entry in tqdm(paper_entries[start_idx:target_idx], desc="Fetching DBLP entries"):
            try:
                paper_info = get_paper_title_and_url(entry)
                paper_info.bibtex = get_paper_bibtex(bibtex_session, entry, req_itv)
                entry_metadata_list.append(paper_info)

                # 即时写入缓存
                save_cache(cache_path, entry_metadata_list)
                time.sleep(req_itv)
            except Exception as e:
                logger.error(f"Error processing entry: {e}")
                continue
    finally:
        bibtex_session.close()
    return entry_metadata_list

# def get_dblp_page_content(url: str, req_itv: float, type: str, count: int = 1) -> list[PaperInfo]:
#
#     # 新增功能：在for entry in tqdm(paper_entries[:target_num]):循环中随时记录信息到cache文件中
#     # 根据url参数先从cache中读取已经访问到的title、url、bibtex
#     # 也就是断点存续
#     # 假设缓存文件已经存在3个paper的信息，那么直接从第四个文件开始
#     # 假如缓存文件不存在或里面没有信息，则从头开始获取
#     # 缓存文件统一放置在一个文件中，位置位于当前文件的上一级目录。要能够根据不同url区分对应的缓存
#
#     res = requests.get(url)
#     if res.status_code != 200:
#         logger.error("{} cannot be loaded. Make sure your input is valid.".format(url))
#         return []
#     soup = BeautifulSoup(res.text, "html.parser")
#     if type == "conf":
#         paper_entries = soup.select(
#             'li.entry.inproceedings[itemscope][itemtype="http://schema.org/ScholarlyArticle"]'
#         )
#     elif type == "journal":
#         paper_entries = soup.select(
#             'li.entry.article[itemscope][itemtype="http://schema.org/ScholarlyArticle"]'
#         )
#     else:
#         logger.error('Invalid type param. Should be "conf" or "journal"')
#
#     entry_metadata_list = list()
#
#     # progress_dblp = tqdm(total=len(paper_entry))
#
#     target_num = len(paper_entries) if count == -1 or count >= len(paper_entries) else count
#     logger.info(f"Total {len(paper_entries)} papers, collect {target_num} of them")
#     logger.debug("Collecting basic info...")
#     bibtex_session = requests.Session()
#     for entry in tqdm(paper_entries[:target_num]):
#         paper_info = get_paper_title_and_url(entry)
#         paper_info.bibtex = get_paper_bibtex(bibtex_session, entry, req_itv)
#         entry_metadata_list.append(paper_info)
#
#         # progress_dblp.update(1)
#
#     bibtex_session.close()
#     # progress_dblp.close()
#
#     return entry_metadata_list


if __name__ == "__main__":
    metadata_list = get_dblp_page_content(get_conf_url("sp", str(2023))[0], 5, "conf")
    # print(title_url_lst)
