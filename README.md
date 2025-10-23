

# Paper Info Crawler

> 本项目仅作学习交流使用，使用该项目造成的后果自行承担

Forked from: [Lraxer's paperinfo_crawler](https://github.com/Lraxer/paperinfo_crawler)

自动化收集会议/期刊论文的基本信息（标题、URL、摘要等），现支持安全四大、软工四大。

已收集的论文信息在`results/`中



## :book: Supported Conference / Journal

| 会议            | -n(--name)参数 | Publisher | 是否支持           |
| --------------- | -------------- | --------- | ------------------ |
| USENIX Security | uss            | USENIX    | :white_check_mark: |
| NDSS            | ndss           | NDSS      | :white_check_mark: |
| CCS             | ccs            | ACM       | :white_check_mark: |
| S&P             | sp             | IEEE      | :white_check_mark: |
| USENIX          | usenix         | USENIX    | :white_check_mark: |
| ICSE            | icse           | ACM       | :white_check_mark: |
| ASE             | ase            | ACM       | :white_check_mark: |
| FSE (<=2023)    | fse            | ACM       | :white_check_mark: |
| ISSTA (<=2024)  | issta          | ACM       | :white_check_mark: |

部分会议会发表在期刊中，发表的年份、位置和卷号难以对应，下表给出部分已支持的会议

| 期刊  | 年份 | -n(--name)参数 | -u(--volume)参数 | Publisher | 是否支持           |
| ----- | ---- | -------------- | ---------------- | --------- | ------------------ |
| FSE   | 2025 | pacmse         | 2                | ACM       | :white_check_mark: |
| ISSTA | 2025 | pacmse         | 2                | ACM       | :white_check_mark: |
| FSE   | 2024 | pacmse         | 1                | ACM       | :white_check_mark: |

:grey_question:**其他**：未在上表中的，还有部分见`src/settings.py`，这些尚未测试，但应该支持




## :rocket: Getting Started

### Install Requirements
```
requests
beautifulsoup4
wheel
bibtexparser
tqdm
zendriver
```

```shell
pip install -r requirements-no-version.txt
```

### Chrome Settings

（目前通过浏览器收集摘要仅支持Chrome）

安装Chrome，并确保chrome的安装路径与`settings.py`中一致

```python
# settings.py
chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
```

### Run

```shell
cd src
python main.py <args>
```

参数说明：

- `-n`/`--name`：会议或期刊名称。支持的会议/期刊对应的参数名称见上表
- `-y`/`--year`：年份（四位数）e.g. 2023
- `-u`/`--volume`：期刊卷号，格式为单个数字，或要爬取的起止卷号，以短横线连接。e.g. 72-79
- `-p`/`--publisher`：指定出版社。正常来说不需要此参数，会根据`name`自动匹配
- `--no-abs`：添加此选项表示不收集摘要。默认收集。
- `--dblp-interval`：从dblp数据库收集论文bibtex的间隔。建议此选项的值不要小于10。
- `--abs-interval`：从出版社收集摘要时的间隔（秒）。建议此项值不要小于10，推荐30秒以上。
- `-c`/`--count`：收集论文的数量。小于0或不传此参数时表示全部收集。
- `-o`/`--output`：输出结果的路径（如果路径不存在会自动创建）。目前仅支持json和markdown格式。
- `--skip`：跳过指定位置的论文。有些论文的url可能无效，导致爬取失败，添加此项以跳过这些论文。


示例：
1. 收集2024年USENIX Security的全部论文
```shell
python main.py --name uss --year 2024 --dblp-interval 10 --abs-interval 60 --output ../results/USENIX/uss-2024.json
```
2. 收集2023年CCS的前270篇论文（共292篇），并跳过221、222号论文
```shell
python main.py --name ccs --year 2024 --dblp-interval 10 --abs-interval 60 --output ../results/CCS/ccs-2024.json --count 270 --skip 221 222
```

3. 收集FSE 2025的所有论文（收录在期刊中）

```shell
python main.py --name pacmse --volume 2 --dblp-interval 10 --abs-interval 60 --output ../results/FSE/fse-2025.json
```

**注意**：

稳妥起见，为了避免ip被封，建议 `dblp-interval`/`abs-interval` 最好设置的大一些，`30`/`60` 比较安全。

## :file_folder: File Structure

```text
├─(chromedriver-user-data)
├─dblp_cache
├─results
│  ├─CCS
│  ├─NDSS
│  ├─S&P
│  ├─USENIX
│  ├─USENIX Security
│  └─...... 
└─src
    ├─crawler
    ├─main.py
    └─settings.py
```
- chromedriver-user-data：运行时，如果使用浏览器爬取会自动生成
- dblp_cache：已收集的dblp数据，可用于加速收集，跳过已收集的论文信息。
- results：已收集的论文数据，可直接使用，不必重复爬取。
- src：源码
  - main.py：程序入口
  - settings.py：支持的会议/期刊，以及一些全局配置
  - crawler：从出版社收集摘要的crawler



## :sparkles: Features

### 断点存续

由于会议一年通常收录几百篇论文，爬取时间会很长，受网络等因素影响，爬取可能会中途失败。

因此较原项目新增了断点存续功能：
- 从dblp爬取信息时，首先尝试从缓存中加载
- 如果指定的输出文件中已存在结果，则会跳过前面的论文
- **每条论文信息在爬取后都会及时保存，因此可以放心中断**


> 注：为了方便实现，本项目是按照dblp给出的论文**顺序**收集并记录缓存/结果，断点存续时也是根据缓存/结果中记录的个数来跳过的，并非根据每篇论文是否保存判断



### 多种保存格式

TODO: 支持以csv、md、json、bibtex多种结果保存

根据output文件后缀自动选择



## :handshake: Contributing

欢迎任何形式的贡献！

- **提交论文收集结果**：提交 Pull Request
    - 新增会议/期刊收集结果的文件到 `results` 对应目录下，命名格式为`{会议缩写}-{年份}.xxx`
    - 如果可以，也请提供 `dblp_cache` 中的对应缓存文件

- **添加对新会议/期刊的支持**：提交 Pull Request
- **其他改进意见和想法**



## :pencil: Note

这里简要介绍工作原理和代码结构，方便阅读和修改

### 核心思想

首先获取会议收录文章的基本信息列表（含每篇论文的doi），再从各大网站上收集摘要

- DBLP数据库收录了各个会议的文章，其url形式规整，可以直接通过会议名称和年份构造
  - 从中可以获取每篇论文的标题、URL、bibtex，但不含摘要
- 访问论文URL，该链接会自动重定向到出版社的页面。接下来脚本尝试从页面中获取摘要


### Workflow

1. 解析参数，根据name获取对出版商，开始收集 (`main.collect_conf_metada`)
2. 根据年份和缩写构造DBLP的URL (`dblp.get_conf_url`)
3. 通过dblp获取所有paper的title和url (`dblp.get_dblp_page_content`)
    1. 解析html获得title
    2. 进一步构造请求并解析得到bibtex，其中包含url
4. 获取摘要 (`main.collect_abstract2`)
    1. 根据出版社获取对应Crawler，根据类型分为两种Crawler
    2. 对每一篇论文调用`crawler.crawl(url)`
    3. 保存数据

### 两种Crawler

根据出版社类型，可以大致将crawler的爬取行为抽象为两种模式：
1. HtmlAbstractCrawler
   - 摘要直接包含在html中
   - 可以直接通过请求获得页面源码，然后解析得到
2. UiAutomationAbstractCrawler
   - 摘要是动态渲染，无法直接从html中获取
   - 或网站对脚本行为有严格检测，很难通过模仿浏览器行为绕过
   - 需要借助浏览器先获取到页面

### 扩展Crawler？

**1. 如果爬取行为符合`HtmlAbstractCrawler`或`UiAutomationAbstractCrawler`**

继承对应类，然后重写对应的抽象方法即可

```python
from .html_abstract_crawler import HtmlAbstractCrawler
from .factory import CrawlerFactory


@CrawlerFactory.register("ndss")
class NDSSAbstractCrawler(HtmlAbstractCrawler):

    @property
    def css_selector(self) -> str:
        return "div.entry-content > div.paper-data > p:nth-child(2) > p"

```

**2. 如果不能归类为以上两种**

继承自`BaseAbstractCrawler`，重写`crawl`方法，还可根据需要重写`prepare`和`stop`

```python
from .base_abstract_crawler import BaseAbstractCrawler
from .factory import CrawlerFactory


@CrawlerFactory.register("new_publisher")
class MyNewAbstractCrawler(BaseAbstractCrawler):

    @property
    def css_selector(self) -> str:
        return "div.entry-content > div.paper-data > p:nth-child(2) > p"

```

**注意：**

不要忘记使用CrawlerFactory注册

```python
@CrawlerFactory.register("new_publisher")
```

需要在`__init__.py`中导入新增crawler文件，这样注册代码才会被执行

```python
from . import factory
from . import usenix_abstract_crawler
from . import ieee_abstract_crawler
from . import acm_abstract_crawler
from . import iospress_abstract_crawler
from . import elsevier_abstract_crawler
from . import ndss_abstract_crawler
```




---

原仓库README

# 爬取论文元数据和摘要

**注意，本项目不会下载论文，仅获取包括摘要在内的论文元数据。**

## 支持的会议/期刊

**包含摘要的 bibtex 文件可以从 [论文元数据仓库](https://github.com/Lraxer/paper_metadata) 获取。** 如果您有包含摘要的 bibtex 或 ris 格式的文件，欢迎向这个仓库提交 PR！

本项目理论上支持 IEEE、ACM、Elsevier、Springer 出版或举办的期刊和会议论文，以及 USENIX、NDSS、IOS Press 等出版社的论文。可参考 [论文元数据收集情况表](https://rigorous-frost-052.notion.site/d5053e59458a47769fd645be500f55ff?v=c97cacf0bdc94d9b965a29f3d5f0d473)，“收录情况”一列不为空的是已经测试过可用的期刊或会议，空的是没有测试或不支持的出版社。

## 安装

Python 版本要求：3.10 及以上。

### 变量设置

1. 安装 Goole Chrome 浏览器，记录 Chrome 可执行文件的路径，例如，Windows 系统下一般是 `C:/Program Files/Google/Chrome/Application/chrome.exe`。
2. 在 `settings.py` 中修改 `chrome_path`，填写 `chrome.exe` 可执行文件的路径。
3. 在 `settings.py` 中修改 `cookie_path`，创建一个目录用于保存 cookie，并填写该目录的路径。
4. （可选）修改 `req_headers`，这个字典用于 requests 库发送请求时设置请求头。

### 设置 Python 虚拟环境与安装依赖

你可以使用 `venv` 或者 `uv` 等工具创建虚拟环境。

```powershell
# For Windows
cd paperinfo_crawler
python -m venv ./venv
.\venv\Scripts\activate
pip install -r requirements-no-version.txt
```

```bash
# For Linux
cd paperinfo_crawler
python -m venv ./venv
source ./venv/bin/activate
pip install -r requirements-no-version.txt
```

## 运行

脚本分为两部分：

1. 从 [dblp](https://dblp.uni-trier.de/) 获取给定会议和年份的论文列表，或给定期刊和卷号的论文列表，得到 bibtex 格式的引用，并获取论文的 `doi.org/xxxx` 格式的 URL 链接。
2. 访问每一篇论文的链接，该链接会自动重定向到出版社的页面。脚本尝试从页面中获取摘要，合并到 bibtex 引用中，生成 `.bib` 文件。

```powershell
cd src
python ./main.py --help

# e.g.
# 会议
python ./main.py -n raid -y 2022 -e -d 5 -t 8
# dblp 上，部分会议一年分为多个part
# 通过 -f 参数，读取pickle文件中保存的dblp论文列表，以获取摘要
# 如果要爬取的会议/期刊不在已验证的支持范围内，用 -p 手动指定出版社
python .\main.py -n iccS -y 2022-2 -p springer -f ./iccS2022-2_dblp.pkl -t 6

# 期刊
python ./main.py -n tifs -u 16 -e -d 5 -t 8
# 可以批量下载多个卷
python ./main.py -n tifs -u 16-18 -e -d 5 -t 8
```

## 测试环境

由于设备有限，当前只在 Windows 11 系统下，Python 3.11.9 环境下运行过脚本。该脚本理论上不受系统限制。

**爬取的速度，即 `-d` 和 `-t` 参数不应太小，以免被封禁。**

## 已知问题

### 人机验证与爬取失败

1. 首先需要保证使用的 IP 具有较高纯净度。
2. 将 Zendriver 的 `headless` 参数设置为 `False`，相比 `True` 的成功率更高。
3. 删除 `settings.py` 中，`cookie_path` 变量指定的目录下的所有文件，重新运行。

### 其他问题

1. 部分带有公式的论文摘要可能无法正确爬取，公式不能正确显示。这是因为网页上的公式经过了渲染，爬到的只是渲染前的原始状态。
2. 部分论文尚未收录在 doi.org 网站上，因此无法通过该链接重定向到出版社的论文页面获取摘要。
3. pvldb 目前无法予以支持。dblp 的链接直接跳转到了 PDF 文件。而 pvldb 官网中很多论文链接是失效的。
