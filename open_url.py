import re
import string
import sublime
import sublime_plugin
import webbrowser

try:
    from MarkdownEditing.wiki_page import *
except ImportError:
    from wiki_page import *

# http://test.com

# ASCII punctuation/whitespace that ends a word/page-name, except '.', '-', '%',
# '_' and '/' which are kept since sign combinations use '.'/'-' (e.g. 𓇴-cob.ra.md),
# URLs use '%' for percent-encoding (e.g. https://phis.me/sigla/document/ARKH%201a/),
# wiki-link page-names use '_' (e.g. char_grid_calibration.md), and subdirectory
# page-names use '/' (e.g. notes/char_grid_calibration.md)
KEEP_CHARS = "._-%/"
TERMINATORS = set(string.whitespace + string.punctuation) - set(KEEP_CHARS)

# A URL runs until whitespace or a character that never occurs unescaped in one,
# so query strings (?id=1&x=2) and fragments (#top) stay attached.
URL_PATTERN = re.compile(r"https?://[^\s<>\"'`\[\]{}|\\^]+")
SENTENCE_PUNCTUATION = ".,;:!?"


def trim_url(url):
    """Drop trailing sentence punctuation and a ')' that closes a markdown link, not the URL."""
    while url and (url[-1] in SENTENCE_PUNCTUATION or (url[-1] == ")" and url.count(")") > url.count("("))):
        url = url[:-1]
    return url


def url_at(line, column):
    for match in URL_PATTERN.finditer(line):
        url = trim_url(match.group())
        if match.start() <= column <= match.start() + len(url):
            return url
    return None


class OpenUrlCommand(sublime_plugin.TextCommand):
    def expand(self, start, end, terminator):
        view_size = self.view.size()

        while (start > 0
                and not self.view.substr(start - 1) in terminator
                and self.view.classify(start) & sublime.CLASS_LINE_START == 0):
            start -= 1

        while (end < view_size
                and not self.view.substr(end) in terminator
                and self.view.classify(end) & sublime.CLASS_LINE_END == 0):
            end += 1

        return start, end

    def run(self, edit):
        s = self.view.sel()[0]
        line = self.view.line(s.a)
        url = url_at(self.view.substr(line), s.a - line.a)
        if url:
            print("URL : " + url)
            webbrowser.open_new_tab(url)
            return

        start, end = self.expand(s.a, s.b, TERMINATORS)
        page_name = self.view.substr(sublime.Region(start, end))
        print("file? " + page_name)
        WikiPage(self.view).select_page(page_name)
            
