import sublime, sublime_plugin
import os, string

try:
    from MarkdownEditing.wiki_page import *
except ImportError:
    from wiki_page import *

try:
    from MarkdownEditing.mdeutils import *
except ImportError:
    from mdeutils import *


class MakeBoldCommand(MDETextCommand):
    # def is_visible(self):
    #     return True

    def run(self, edit):
        print("Running MakeBoldCommand")        
        wiki_page = WikiPage(self.view)
        region = wiki_page.select_word_at_cursor()
        begin = region.begin()
        end = region.end()
        self.view.insert(edit, end, "**")
        self.view.insert(edit, begin, "**")
