import logging.config
import os
import random
import sys
import argparse
import pickle
import traceback

import bibtexparser
import bibtexparser.model

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
logging.config.fileConfig("logging.conf")
logger = logging.getLogger()
for noisy_logger in ["websockets", "asyncio", "zendriver", "urllib3", "uc.connection"]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)


import dblp
from settings import cj_pub_dict
from src.data import PaperInfo

from src.save_result import save_result, get_result_num
from crawler.factory import get_crawler
import utils

# logger.setLevel(logging.DEBUG)
# handler = logging.StreamHandler()
# handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# handler.setFormatter(formatter)
# logger.addHandler(handler)


# publisher_module_dict = {
#     "ieee": entry_ieee,
#     "acm": entry_acm,
#     "springer": entry_springer,
#     "usenix": entry_usenix,
#     "ndss": entry_ndss,
#     "elsevier": entry_elsevier,
#     "iospress": entry_iospress,
# }


def collect_conf_metadata(
    name: str,
    year: str,
    publisher: str,
    need_abstract: bool,
    dblp_req_itv: float,
    abs_itv: int,
    save_pickle: bool,
    output: str,
    count: int = -1,
    skip: list[int] = [],
) -> list[PaperInfo]:

    # 构造dblp的url
    conf_url, entry_type_in_url = dblp.get_conf_url(name, year)
    if conf_url is None:
        logger.error("Cannot get dblp URL for {}, {}".format(name, year))
        return []

    # 通过dblp获取所有paper的title和url
    existed_num = get_result_num(file_path=output)
    entry_metadata_list: list[PaperInfo] = dblp.get_dblp_page_content(url=conf_url, req_itv=dblp_req_itv, type=entry_type_in_url, existed_num=existed_num, count=count)
    logger.debug("Number of papers: {}".format(len(entry_metadata_list)))
    if len(entry_metadata_list) <= 0:
        logger.warning("No paper found in {}, {}".format(name, year))
        return []

    if save_pickle:
        pkl_filename = "{}{}_dblp.pkl".format(name, year)
        logger.debug("Save collected dblp data to {}.".format(pkl_filename))
        with open(pkl_filename, "wb") as f:
            pickle.dump(entry_metadata_list, f)

    if need_abstract:
        collect_abstract2(entry_metadata_list=entry_metadata_list, publisher=publisher, output=output, req_itv=abs_itv, count=count, skip=skip)
    return entry_metadata_list


def collect_journal_metadata(
    name: str,
    volume: str,
    publisher: str,
    need_abstract: bool,
    output: str,
    dblp_req_itv: float,
    abs_itv: int,
    save_pickle: bool,
    count: int = -1,
    skip: list[int] = [],
) -> list:
    existed_num = get_result_num(file_path=output)
    entry_metadata_list = dblp.get_dblp_page_content(
        dblp.get_journal_url(name, volume), dblp_req_itv, "journal", existed_num=existed_num, count=count
    )
    logger.debug("Number of papers: {}".format(len(entry_metadata_list)))
    if len(entry_metadata_list) <= 0:
        logger.warning("No paper found in {}, {}.".format(name, volume))
        return []

    if save_pickle:
        pkl_filename = "{}{}_dblp.pkl".format(name, volume)
        logger.debug("Save collected dblp data to {}.".format(pkl_filename))
        with open(pkl_filename, "wb") as f:
            pickle.dump(entry_metadata_list, f)

    if need_abstract:
        # asyncio.run(
        #     collect_abstract(
        #         name,
        #         entry_metadata_list,
        #         export_bib_path,
        #         publisher,
        #         dblp_req_itv,
        #     )
        # )
        collect_abstract2(entry_metadata_list, publisher, output, req_itv=abs_itv, count=count, skip=skip)

    return entry_metadata_list


def collect_abstract2(
    entry_metadata_list: list[PaperInfo],
    publisher: str,
    output: str,
    count: int,
    req_itv: float = 10,
    skip: list[int] = []
):

    logger.info("Publisher: {}.".format(publisher))

    crawler = get_crawler(publisher, interval=req_itv)
    logger.info(f"Get crawler: {crawler.__class__.__name__}")
    try:
        crawler.prepare()
        # 获取已经爬取的数量
        start_idx = get_result_num(file_path=output)
        end_idx = len(entry_metadata_list) if count < 0 else start_idx + count
        for i, paper in enumerate(entry_metadata_list[start_idx:end_idx]):
            logger.info(f"[{i+start_idx+1}] '{paper.title}'")
            logger.info(f"[{i+start_idx+1}] URL: {paper.url}")
            if i+start_idx+1 in skip:
                logger.critical("SKIP this one")
                continue
            abstract = crawler.crawl(paper.url)
            paper.abstract = abstract

            # update paper's bib as well
            tmp_library = bibtexparser.parse_string(paper.bibtex)
            if len(tmp_library.entries) != 1:
                logger.warning(
                    'Cannot parse bibtex string to entry of paper "{}", string is: {}.'.format(
                        paper.title, repr(paper.bibtex)
                    )
                )
            else:
                abstract_field = bibtexparser.model.Field("abstract", repr(abstract)[1:-1])
                tmp_library.entries[0].set_field(abstract_field)
                paper.bibtex = bibtexparser.write_string(tmp_library)

            save_result(file_path=output, papers=[paper], detailed=False)

            rand_int = random.randint(-10, 10)
            sleep_time = req_itv + rand_int
            logger.info(f"Sleep for {sleep_time}s...")
            utils.count_down(seconds=int(sleep_time))
    except Exception:
        logger.error(traceback.format_exc())
    finally:
        # stop web driver if needed
        crawler.stop()


def collect_abstract_from_dblp_pkl(
    pkl_filename: str,
    name: str,
    publisher: str,
    output: str,
    req_itv: float,
):
    raise NotImplementedError
    with open(pkl_filename, "rb") as f:
        entry_metadata_list = pickle.load(f)
    collect_abstract2(entry_metadata_list, publisher, output, req_itv)


def main():
    parser = argparse.ArgumentParser(description="Collect paper metadata.")

    parser.add_argument("--name", "-n", type=str, required=True, help="会议/期刊标识")

    # conference or journal
    grp1 = parser.add_mutually_exclusive_group(required=True)
    grp1.add_argument("--year", "-y", type=str, default=None, help="会议举办时间（年）e.g. 2023")
    grp1.add_argument("--volume", "-u", type=str, default=None, help="期刊卷号，格式为单个数字，或要爬取的起止卷号，以短横线连接。e.g. 72-79")

    parser.add_argument("--publisher", "-p", type=str, default=None, help="指定出版社")
    parser.add_argument(
        "--save-pkl",
        "-e",
        action="store_true",
        default=False,
        help="是否将从dblp收集的元数据保存到pickle文件，默认名称为[name][year/volume]_dblp.pkl, 对于期刊，该选项只支持volume为数字的输入（e.g. -u 72），不支持多卷的输入（e.g. -u 72-79）",
    )
    parser.add_argument(
        "--no-abs",
        action="store_true",
        default=False,
        help="是否从出版社网站收集摘要，设置此选项表示不收集摘要",
    )
    parser.add_argument(
        "--from-pkl",
        "-f",
        type=str,
        default=None,
        help="从pickle加载dblp元数据，并收集摘要",
    )
    parser.add_argument(
        "--dblp-interval",
        type=float,
        default=10,
        help="向dblp发送请求的间隔（秒）",
    )
    parser.add_argument(
        "--abs-interval", type=float, default=10, help="收集摘要的请求发送间隔（秒）"
    )
    # 保存不含摘要的bibtex不在设计意图内
    parser.add_argument(
        "--save",
        "-s",
        type=str,
        default=None,
        help="bibtex文件的保存位置，默认是[name][year].bib, 对于期刊，该选项只支持volume为数字的输入（e.g. -u 72），不支持多卷的输入（e.g. -u 72-79）",
    )

    parser.add_argument("-c", "--count", type=int, default=-1)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--skip", action='extend', type=int, nargs='+', default=[])

    args = parser.parse_args()

    name = args.name

    save_pkl = args.save_pkl
    need_abs = not args.no_abs
    from_pkl_fn = args.from_pkl

    publisher = cj_pub_dict.get(args.name)
    if args.publisher is not None:
        if publisher is None:
            if from_pkl_fn is not None:
                print(
                    "This conference/journal has not been tested yet. Setting --save-pkl is recommended."
                )
            publisher = args.publisher
        elif publisher != args.publisher:
            print("Input publisher cannot match.")
            selection = input(
                'Use (1) pre-set publisher "{}" or (2) your input "{}"? Input 1 or 2.'.format(
                    publisher, args.publisher
                )
            )
            if selection == "1":
                logger.debug("Use pre-set publisher.")
            else:
                logger.debug("Use user input.")
                publisher = args.publisher
    else:
        if publisher is None:
            logger.error("Cannot find this conference/journal. Please specify publisher by -p or --publisher.")
            exit(1)

    if need_abs is False and from_pkl_fn is not None:
        logger.error("--no-abs cannot be set together with --from-pkl (-f).")
        exit(1)

    dblp_req_itv = args.dblp_interval
    # 收集摘要的发送请求时间间隔
    abs_itv = args.abs_interval

    if args.year is None:
        # Journal
        volume: str = args.volume

        if args.save is None:
            saved_fn = "{}{}.bib".format(name, volume)
        else:
            saved_fn = args.save

        logger.debug(
            "\nname:{}\nvolume:{}\nneed_abs:{}\ndblp_req_itv:{}\nreq_itev:{}\npublisher:{}\nsave_pkl:{}\nfrom_pkl_fn:{}\n".format(
                name,
                volume,
                need_abs,
                dblp_req_itv,
                abs_itv,
                publisher,
                save_pkl,
                from_pkl_fn,
            )
        )
        # format: 19
        if volume.isdigit():
            if args.save is None:
                saved_fn = "{}{}.bib".format(name, volume)
            else:
                saved_fn = args.save
            # logger.debug("saved_fn:{}".format(saved_fn))
            if from_pkl_fn is None:
                collect_journal_metadata(
                    name, volume, publisher, need_abs, args.output, dblp_req_itv, abs_itv, save_pkl, count=args.count, skip=args.skip
                )
                exit(0)
            else:
                collect_abstract_from_dblp_pkl(
                    from_pkl_fn, name, publisher, args.output, abs_itv
                )
                exit(0)

        # format: 19-29
        vol_list = volume.split("-")
        if len(vol_list) != 2:
            logger.error("Invalid volume input.")
            exit(1)
        start_vol = int(vol_list[0])
        end_vol = int(vol_list[1])

        if end_vol <= start_vol:
            logger.error("Invalid volume input.")
            exit(1)

        if from_pkl_fn is not None:
            logger.error(
                '--from-pkl (-f) is not compatible with "72-79" format of volume parameter.'
            )
            exit(1)

        for vol in range(start_vol, end_vol + 1):
            saved_fn = "{}{}.bib".format(name, vol)
            collect_journal_metadata(
                name, str(vol), publisher, need_abs, args.output, dblp_req_itv, abs_itv, save_pkl, count=args.count, skip=args.skip
            )
    else:
        # Conference
        year = args.year

        logger.debug(
            "\nname:{}\nyear:{}\nneed_abs:{}\ndblp_req_itv:{}\nreq_itev:{}\npublisher:{}\nsave_pkl:{}\nfrom_pkl_fn:{}\n".format(
                name,
                year,
                need_abs,
                dblp_req_itv,
                abs_itv,
                publisher,
                save_pkl,
                from_pkl_fn,
            )
        )
        if from_pkl_fn is None:
            paper_list = collect_conf_metadata(
                name, year, publisher, need_abs, dblp_req_itv, abs_itv, save_pkl,
                output=args.output, count=args.count, skip=args.skip
            )
            # save_result(file_path=args.output, papers=paper_list, detailed=False)
            # for item in paper_list:
            #     logger.info('=' * 50)
            #     logger.info(f'Title: {item.title}')
            #     logger.info(f'URL: {item.url}')
            #     logger.info(f'Abstract: {item.abstract}')
        else:
            logger.debug("Collect abstract from dblp pickle file.")
            collect_abstract_from_dblp_pkl(
                from_pkl_fn, name, publisher, args.output, abs_itv
            )


if __name__ == "__main__":

    logger.info("test")
    main()