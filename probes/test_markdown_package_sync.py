"""The generated Markdown.sublime-package must track MDE's own syntaxes, not stay a stale snapshot."""
import os, shutil, sys, types, unittest
from zipfile import ZipFile

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGES_DIR = os.path.dirname(PLUGIN_DIR)
INSTALLED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "installed_packages")
PACKAGE_PATH = os.path.join(INSTALLED_DIR, "Markdown.sublime-package")


def load_resource(resource):
    with open(os.path.join(PACKAGES_DIR, resource[len("Packages/"):]), encoding="utf-8") as f:
        return f.read()


sublime = types.ModuleType("sublime")
sublime.load_resource = load_resource
sublime.installed_packages_path = lambda: INSTALLED_DIR
sublime.load_settings = lambda name: types.SimpleNamespace(get=lambda key, default=None: default)
sys.modules["sublime"] = sublime
color_schemes = types.ModuleType("MarkdownEditing.plugins.color_schemes")
color_schemes.clear_color_schemes = color_schemes.clear_invalid_color_schemes = color_schemes.select_color_scheme = None
sys.modules["MarkdownEditing.plugins.color_schemes"] = color_schemes
sys.path.insert(0, PACKAGES_DIR)

from MarkdownEditing.plugins.bootstrap import augment_default_markdown


def packaged_syntax(name):
    with ZipFile(PACKAGE_PATH) as pkg:
        return pkg.read(name).decode("utf-8")


class MarkdownPackageSyncTest(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(INSTALLED_DIR, ignore_errors=True)
        os.makedirs(INSTALLED_DIR)

    def tearDown(self):
        shutil.rmtree(INSTALLED_DIR, ignore_errors=True)

    def test_stale_package_is_regenerated(self):
        with ZipFile(PACKAGE_PATH, "w") as pkg:
            pkg.writestr("MultiMarkdown.sublime-syntax", "stale")
        augment_default_markdown()
        self.assertIn("extends: Markdown.sublime-syntax", packaged_syntax("MultiMarkdown.sublime-syntax"))
        self.assertIn("file_extensions:", packaged_syntax("Markdown.sublime-syntax"))

    def test_up_to_date_package_is_left_alone(self):
        augment_default_markdown()
        first_write = os.path.getmtime(PACKAGE_PATH)
        os.utime(PACKAGE_PATH, (0, 0))
        augment_default_markdown()
        self.assertEqual(os.path.getmtime(PACKAGE_PATH), 0)
        self.assertNotEqual(first_write, 0)


if __name__ == "__main__":
    unittest.main()
