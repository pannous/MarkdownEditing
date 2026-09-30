"""Wiki links must resolve next to the current file before any fallback dir."""
import os, sys, types, unittest

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_DIR)
sys.modules.setdefault("sublime", types.ModuleType("sublime"))
sys.modules.setdefault("sublime_plugin", types.ModuleType("sublime_plugin"))

from wiki_page import WikiPage, slugify

CHINESE_DIR = "/Users/me/Documents/uruk_egypt.nosync/chinese"
FALLBACK_DIR = "/Users/me/Documents/uruk_egypt.nosync/docs"
FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


class FakeView:
    def __init__(self, file_name):
        self._file_name = file_name

    def file_name(self):
        return self._file_name

    def settings(self):
        return types.SimpleNamespace(get=lambda key, default=None: default)


class WikiPageResolutionTest(unittest.TestCase):
    def resolve(self, current_file, pagename):
        return [path for _, path in WikiPage(FakeView(current_file)).find_files_with_name(pagename)]

    def test_prefers_page_next_to_current_file(self):
        hits = self.resolve(os.path.join(CHINESE_DIR, "progress.md"), "mnemonics")
        self.assertIn(os.path.join(CHINESE_DIR, "mnemonics.md"), hits)
        self.assertNotIn(os.path.join(FALLBACK_DIR, "mnemonics.md"), hits)

    def test_falls_back_when_page_is_absent_locally(self):
        hits = self.resolve(os.path.join(CHINESE_DIR, "progress.md"), "_Sidebar")
        self.assertEqual(hits, [os.path.join(FALLBACK_DIR, "_Sidebar.md")])

    def test_spaces_in_link_match_dashes_in_filename(self):
        hits = self.resolve(os.path.join(FALLBACK_DIR, "index.md"), "amun ra")
        self.assertEqual(hits, [os.path.join(FALLBACK_DIR, "amun-ra.md")])

    def test_existing_file_with_own_extension_is_used_as_is(self):
        hits = self.resolve(os.path.join(FIXTURES_DIR, "index.md"), "uniscript.wasp")
        self.assertEqual(hits, [os.path.join(FIXTURES_DIR, "uniscript.wasp")])

    def test_new_page_name_uses_dashes_for_spaces(self):
        self.assertEqual(slugify("amun ra"), "amun-ra")


if __name__ == "__main__":
    unittest.main()
