"""Delete in front of a heading's hashes and shift+tab anywhere in a heading lower its level; at level 1 the hashes go.
Runs the real mde_change_headings_level on a minimal in-memory view, plus checks the OSX keymap bindings."""
import json, os, re, sys, types, unittest

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(PACKAGE_DIR))

sublime = types.ModuleType("sublime")
sublime.View = object
sublime.Region = None
sublime_plugin = types.ModuleType("sublime_plugin")
sublime_plugin.TextCommand = sublime_plugin.ViewEventListener = sublime_plugin.EventListener = object
sys.modules.setdefault("sublime", sublime)
sys.modules.setdefault("sublime_plugin", sublime_plugin)


class Region:
    def __init__(self, a, b=None):
        self.a, self.b = a, a if b is None else b

    def begin(self):
        return min(self.a, self.b)

    def end(self):
        return max(self.a, self.b)


sublime.Region = Region


class Selection(list):
    def clear(self):
        del self[:]

    def add(self, region):
        self.append(region)

    def add_all(self, regions):
        self.extend(regions)


class FakeView:
    def __init__(self, text, caret):
        self.text, self.selection = text, Selection([Region(caret)])

    def settings(self):
        return {"mde.match_heading_hashes": False}

    def sel(self):
        return self.selection

    def split_by_newlines(self, region):
        return [region]

    def line(self, region):
        start = self.text.rfind("\n", 0, region.begin()) + 1
        end = self.text.find("\n", region.begin())
        return Region(start, len(self.text) if end < 0 else end)

    def substr(self, region):
        return self.text[region.begin():region.end()]

    def rowcol(self, point):
        return self.text.count("\n", 0, point), point - (self.text.rfind("\n", 0, point) + 1)

    def replace(self, edit, region, string):
        self.text = self.text[:region.begin()] + string + self.text[region.end():]

    def show(self, *args):
        pass


from MarkdownEditing.plugins.headings.level import MdeChangeHeadingsLevelCommand


def lower_heading(text, caret):
    command = MdeChangeHeadingsLevelCommand.__new__(MdeChangeHeadingsLevelCommand)
    command.view = FakeView(text, caret)
    command.run(None, by=-1)
    return command.view.text


def osx_bindings(key):
    with open(os.path.join(PACKAGE_DIR, "Default (OSX).sublime-keymap"), encoding="utf-8") as keymap:
        source = re.sub(r"^\s*//.*$", "", keymap.read(), flags=re.M)
    return [binding for binding in json.loads(re.sub(r",(\s*[\]}])", r"\1", source)) if binding["keys"] == [key]]


class HeadingLevelKeysTest(unittest.TestCase):
    def test_level_one_heading_loses_its_hash(self):
        self.assertEqual(lower_heading("# <:gardiner Q4A>\ntext", 0), "<:gardiner Q4A>\ntext")

    def test_level_two_becomes_level_one(self):
        self.assertEqual(lower_heading("## Title", 0), "# Title")

    def test_shift_tab_lowers_headings_wherever_the_caret_is(self):
        heading_bindings = [b for b in osx_bindings("shift+tab") if b["command"] == "mde_change_headings_level"]
        self.assertEqual(len(heading_bindings), 1)
        self.assertEqual(heading_bindings[0]["args"], {"by": -1})
        selectors = [c["operand"] for c in heading_bindings[0]["context"] if c["key"] == "selector"]
        self.assertTrue(any("markup.heading" in selector for selector in selectors))
        self.assertFalse(any(c["key"] in ("preceding_text", "following_text") for c in heading_bindings[0]["context"]))


if __name__ == "__main__":
    unittest.main()
