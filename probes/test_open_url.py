"""Clicking/opening a URL must open the whole URL, including query strings and fragments."""
import os, sys, types, unittest

PACKAGES_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PACKAGES_DIR)


class Region:
    def __init__(self, a, b):
        self.a, self.b = a, b


sublime = types.ModuleType("sublime")
sublime.View = object
sublime.Region = Region
sublime.CLASS_LINE_START, sublime.CLASS_LINE_END = 1, 2
sublime_plugin = types.ModuleType("sublime_plugin")
sublime_plugin.TextCommand = sublime_plugin.ViewEventListener = object
sys.modules.setdefault("sublime", sublime)
sys.modules.setdefault("sublime_plugin", sublime_plugin)

import MarkdownEditing.open_url as open_url


class FakeView:
    def __init__(self, text, cursor):
        self.text, self.cursor = text, cursor

    def size(self):
        return len(self.text)

    def sel(self):
        return [Region(self.cursor, self.cursor)]

    def substr(self, x):
        return self.text[x.a:x.b] if isinstance(x, Region) else self.text[x]

    def line(self, point):
        return Region(self.text.rfind("\n", 0, point) + 1, (self.text + "\n").find("\n", point))

    def classify(self, point):
        return (point == 0 or self.text[point - 1] == "\n") * 1 | (point == len(self.text) or self.text[point] == "\n") * 2


def opened_url(text, clicked_at):
    opened = []
    open_url.webbrowser.open_new_tab = opened.append
    command = open_url.OpenUrlCommand()
    command.view = FakeView(text, text.index(clicked_at))
    command.run(None)
    return opened[0] if opened else None


HN = "https://news.ycombinator.com/item?id=28657358"


class OpenUrlTest(unittest.TestCase):
    def test_query_string_is_kept(self):
        self.assertEqual(opened_url("see " + HN + " here", "news"), HN)

    def test_click_inside_query_string(self):
        self.assertEqual(opened_url("see " + HN + " here", "28657"), HN)

    def test_fragment_and_ampersand(self):
        url = "https://example.com/a?b=1&c=2#frag"
        self.assertEqual(opened_url("x " + url + ", y", "example"), url)

    def test_markdown_link_and_sentence_end(self):
        self.assertEqual(opened_url("[hn](" + HN + ").", "item"), HN)

    def test_balanced_parentheses(self):
        url = "https://en.wikipedia.org/wiki/Mercury_(planet)"
        self.assertEqual(opened_url("see " + url + ".", "wiki"), url)


if __name__ == "__main__":
    unittest.main()
