import sublime, sublime_plugin
import os, string
import re


DEFAULT_MARKDOWN_EXTENSION = '.md'
PAGE_REF_FORMAT = '[[%s]]'
DEFAULT_HOME_PAGE = "HomePage"
# Searched only when a page isn't found next to the current file.
FALLBACK_SEARCH_DIRS = ["/Users/me/Documents/uruk_egypt.nosync/docs"]


def current_dir_of(view):
    try:
        return os.path.dirname(view.file_name())
    except:
        return os.path.dirname(".")


WORD_SEPARATORS = " -_"


def escape_pagename(name):
    """Any of " -_" in a wiki link matches any of them in a filename."""
    separators = "[%s]" % re.escape(WORD_SEPARATORS)
    return "".join(separators if char in WORD_SEPARATORS else re.escape(char) for char in name)


def slugify(name):
    """Filename spelling for a new page: spaces become dashes."""
    return name.replace(" ", "-")


def search_dirs_for(current_dir):
    dirs = [current_dir, os.path.join(current_dir, "auto")]
    dirs.extend(d for d in FALLBACK_SEARCH_DIRS if os.path.isdir(d) and d != current_dir)
    return dirs


class WikiPage:
    def __init__(self, view):
        self.view = view

    def identify_page_at_cursor(self):
        for region in self.view.sel():
            text_on_cursor = None
            pos = region.begin()
            scope_region = self.view.extract_scope(pos)
            if not scope_region.empty():
                text_on_cursor = self.view.substr(scope_region)
                lines = text_on_cursor.split("\n")
                if(len(lines)>1):
                    print("please click on word first")
                    return self.view.sel()
                else:
                    return text_on_cursor.strip("[] \t")

        return None
        
# a[[ok]]c
    def select_page(self, pagename):
        pagename = re.sub(r'.*\[','',pagename)
        pagename = re.sub(r'\].*','',pagename)
        print("Open page: %s" % (pagename))
        if "\n" in pagename:
            print("newline in pagename … abort!")
            return []
        if pagename:
            self.file_list = self.find_files_with_name(pagename)

        if len(self.file_list) > 1:
            self.view.window().show_quick_panel(self.file_list, self.open_selected_file)
        elif len(self.file_list) == 1:
            self.open_selected_file(0)
        else:
            self.open_new_file(pagename)


    def find_files_with_name(self, pagename):
        if "\n" in pagename:
            print("newline in pagename … abort!")
            return []
        pagename = pagename.replace('\\', os.sep).replace(os.sep+os.sep, os.sep).strip()

        self.current_file = self.view.file_name()
        self.current_dir = current_dir_of(self.view)
        print("Locating page '%s' in: %s" % (pagename, self.current_dir) )

        markdown_extension = self.view.settings().get("mde.wikilinks.markdown_extension", DEFAULT_MARKDOWN_EXTENSION)

        # A pagename may include subdirectories, e.g. "notes/char_grid_calibration.md" -
        # match the basename against filenames, then require the containing
        # directory to end with the given subdirectory so the right file wins.
        subdir, basename = os.path.split(pagename)

        # A name with its own extension, e.g. "uniscript.wasp", may be an existing file as-is.
        if basename.endswith(markdown_extension):
            search_pattern = "^%s$" % escape_pagename(basename)
        elif "." in basename:
            search_pattern = "^%s(%s)?$" % (escape_pagename(basename), re.escape(markdown_extension))
        else:
            search_pattern = "^%s%s$" % (escape_pagename(basename), re.escape(markdown_extension))

        results = []
        for search_dir in search_dirs_for(self.current_dir):
            results.extend(self.scan_dir_tree_for_pattern(search_dir, search_pattern, subdir))
            if results:
                break

        return results

    def scan_dir_tree_for_pattern(self, search_dir, search_pattern, subdir=""):
        results = []
        for dirname, _, files in self.list_dir_tree(search_dir):
            if subdir and not dirname.replace(os.sep, "/").endswith(subdir.replace(os.sep, "/")):
                continue
            for file in files:
                if re.search(search_pattern, file, re.IGNORECASE):
                    filename = os.path.join(dirname, file)
                    results.append([self.extract_pagename(filename), filename])

        return results

    def find_files_with_ref(self):
        self.current_file = self.view.file_name()
        self.current_dir, current_base = os.path.split(self.current_file)
        self.current_name, _ = os.path.splitext(current_base)

        markdown_extension = self.view.settings().get("mde.wikilinks.markdown_extension", DEFAULT_MARKDOWN_EXTENSION)

        results = []
        for dirname, _, files in self.list_dir_tree(self.current_dir):
            for file in files:
                pagename, extension = os.path.splitext(file)
                filename = os.path.join(dirname, file)
                if extension == markdown_extension and self.contains_ref(filename, self.current_name):
                    results.append([pagename, filename])

        return results


    def contains_ref(self, filename, pagename):
        link_text = PAGE_REF_FORMAT % pagename

        try:
            if link_text in open(filename).read():
                return True
        except:
            pass

        return False


    def select_backlink(self, file_list):
        if file_list:
            self.file_list = file_list
            self.view.window().show_quick_panel(self.file_list, self.open_selected_file)
        else:
            msg = "No pages reference this page"
            print(msg)
            self.view.window().status_message(msg)


    def open_new_file(self, pagename):
        current_syntax = self.view.settings().get('syntax')
        current_dir = current_dir_of(self.view)

        markdown_extension = self.view.settings().get("mde.wikilinks.markdown_extension", DEFAULT_MARKDOWN_EXTENSION)

        pagename = slugify(pagename)
        if pagename.endswith(markdown_extension):
            filename = os.path.join(current_dir, pagename)
        else:
            filename = os.path.join(current_dir, pagename + markdown_extension)

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        new_view = self.view.window().new_file()
        new_view.retarget(filename)
        new_view.run_command('prepare_from_template', {
            'title': pagename,
            'template': 'default_page'
        })
        print("Current syntax: %s" % current_syntax)
        new_view.set_syntax_file(current_syntax)

        # Create but don't save page
        # new_view.run_command('save')


    def open_selected_file(self, selected_index):
        if selected_index != -1:
            _, file = self.file_list[selected_index]
            
            print("Opening file '%s'" % (file))
            self.view.window().open_file(file)

# abc[[ok]]def
    def extract_pagename(self, filename):
        _, base_name = os.path.split(filename)
        pagename, _ = os.path.splitext(base_name)
        # pagename = pagename.replace("[[","").replace("]]","")
        pagename = re.sub(r'.*\[','',pagename)
        pagename = re.sub(r'\].*','',pagename)
        return pagename;


    def list_dir_tree(self, directory):
        for dir, dirnames, files in os.walk(directory):
            dirnames[:] = [dirname for dirname in dirnames]
            yield dir, dirnames, files

    def select_word_at_cursor(self):
        word_region = None
        print("select_word_at_cursor")

        selection = self.view.sel()
        for region in selection:
            word_region = self.view.word(region)
            if not word_region.empty():
                selection.clear()
                selection.add(word_region)
                return word_region

        return word_region

    def show_quick_list(self, file_list):        
        self.file_list = file_list

        window = self.view.window()
        window.show_quick_panel(file_list, self.replace_selection_with_pagename)


    def replace_selection_with_pagename(self, selected_index):
        if selected_index != -1:
            pagename, file = self.file_list[selected_index]
            
            print("Using selected page '%s'" % (pagename))
            self.view.run_command('replace_selected', {'text': pagename})


    def find_matching_files(self, word_region):
        word = None if word_region.empty() else self.view.substr(word_region)

        current_file = self.view.file_name()
        current_dir, current_base = os.path.split(current_file)
        print("Finding matching files for %s in %s" % (word, current_dir))

        markdown_extension = self.view.settings().get("mde.wikilinks.markdown_extension", DEFAULT_MARKDOWN_EXTENSION)

        # Optionally strip extension...
        if word is not None and word.endswith(markdown_extension):
            word = word[:-len(markdown_extension)]

        # Scan directory tree for potential filenames that contain the word...
        results = []
        for dirname, _, files in self.list_dir_tree(current_dir):
            for file in files:
                pagename, extension = os.path.splitext(file)
                filename = os.path.join(dirname, file)

                if extension == markdown_extension and (not word or word in pagename):
                    results.append([pagename, filename])

        return results


    def make_page_reference(self, edit, region):
        print("Make page reference %s" % region)

        begin = region.begin()
        end = region.end()

        self.view.insert(edit, end, "]]")
        self.view.insert(edit, begin, "[[")

        if region.empty():
            region = sublime.Region(begin+2, end+2)

            selection = self.view.sel()
            selection.clear()
            selection.add(region)
