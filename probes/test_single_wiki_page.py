"""F12 (mde_open_page) and clicks (open_url) must share one WikiPage with the custom link resolution."""
import os, sys, types, unittest

PACKAGES_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PACKAGES_DIR)

sublime = types.ModuleType("sublime")
sublime.View = object
sublime_plugin = types.ModuleType("sublime_plugin")
sublime_plugin.TextCommand = sublime_plugin.ViewEventListener = object
sys.modules.setdefault("sublime", sublime)
sys.modules.setdefault("sublime_plugin", sublime_plugin)

import MarkdownEditing.wiki_page as custom
import MarkdownEditing.plugins.wiki_page as commands


class SingleWikiPageTest(unittest.TestCase):
    def test_mde_commands_use_the_custom_wiki_page(self):
        self.assertIs(commands.WikiPage, custom.WikiPage)


if __name__ == "__main__":
    unittest.main()
