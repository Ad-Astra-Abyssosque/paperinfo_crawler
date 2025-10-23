class PaperInfo:

    def __init__(self, title, url, bibtex=''):
        self.title = title
        self.url = url
        self.abstract = ''
        self.bibtex: str = bibtex

    def __str__(self) -> str:
        return f"Title: {self.title}\nURL: {self.url}\nAbstract:\n{self.abstract}"
