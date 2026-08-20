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

# Once a token is confirmed to be a real http(s) scheme, ':' and '/' are part
# of the URL too (e.g. the "://" and path separators), so they stop being
# terminators for that expansion only - everything else still cuts a URL off.
URL_KEEP_CHARS = KEEP_CHARS + ":/"
URL_TERMINATORS = set(string.whitespace + string.punctuation) - set(URL_KEEP_CHARS)

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

        # Expand selection to possible URL/page-name
        start, end = self.expand(s.a, s.b, TERMINATORS)
        url = self.view.substr(sublime.Region(start, end))

        # If this is really an http(s) scheme, re-expand keeping ':' and '/'
        # so the full URL (not just "http") is captured.
        if url in ("http", "https") and self.view.substr(sublime.Region(end, end + 3)) == "://":
            start, end = self.expand(start, end, URL_TERMINATORS)
            url = self.view.substr(sublime.Region(start, end))

        if url.startswith(('http://', 'https://')):
            print("URL : " + url)
            webbrowser.open_new_tab(url)
        else:
            print("file? " + url)
            wiki_page = WikiPage(self.view)
            wiki_page.select_page(url)
            
