import string
import sublime
import sublime_plugin
import webbrowser

try:
    from MarkdownEditing.wiki_page import *
except ImportError:
    from wiki_page import *

# http://test.com

# ASCII punctuation/whitespace that ends a word/page-name, except '.', '-' and '%'
# which are kept since sign combinations use '.'/'-' (e.g. 𓇴-cob.ra.md) and URLs
# use '%' for percent-encoding (e.g. https://phis.me/sigla/document/ARKH%201a/)
KEEP_CHARS = ".-%"
TERMINATORS = set(string.whitespace + string.punctuation) - set(KEEP_CHARS)

class OpenUrlCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        s = self.view.sel()[0]

        # Expand selection to possible URL
        start = s.a
        end = s.b

        view_size = self.view.size()
        terminator = TERMINATORS

        while (start > 0
                and not self.view.substr(start - 1) in terminator
                and self.view.classify(start) & sublime.CLASS_LINE_START == 0):
            start -= 1

        while (end < view_size
                and not self.view.substr(end) in terminator
                and self.view.classify(end) & sublime.CLASS_LINE_END == 0):
            end += 1

        # Check if this is URL
        url = self.view.substr(sublime.Region(start, end))

        if url.startswith(('http://', 'https://')):
            print("URL : " + url)
            webbrowser.open_new_tab(url)
        else:
            print("file? " + url)
            wiki_page = WikiPage(self.view)
            wiki_page.select_page(url)
            
