import sublime, sublime_plugin
import os, string
import re


DEFAULT_MARKDOWN_EXTENSION = '.md'
PAGE_REF_FORMAT = '[[%s]]'
DEFAULT_HOME_PAGE = "HomePage"


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
                    return text_on_cursor.strip(string.punctuation)

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
        try:
            self.current_dir = os.path.dirname(self.current_file)
        except:
            self.current_dir = os.path.dirname(".")
        if "uruk_egypt" in self.current_dir and not "docs" in self.current_dir:
            self.current_dir = os.path.dirname("/Users/me/Documents/uruk_egypt/docs/")
        print("Locating page '%s' in: %s" % (pagename, self.current_dir) )

        markdown_extension = self.view.settings().get("mde.wikilinks.markdown_extension", DEFAULT_MARKDOWN_EXTENSION)


        # Optionally strip extension...
        try:
            if pagename.endswith(markdown_extension):
                search_pattern = "^%s$" % pagename
            else:
                search_pattern = "^%s%s$" % (pagename, markdown_extension)
        except: pass

        # Scan directory tree for files that match the pagename...
        results = []
        for dirname, _, files in self.list_dir_tree(self.current_dir):
            for file in files:
                if re.search(search_pattern, file, re.IGNORECASE):
                    filename = os.path.join(dirname, file)
                    results.append([self.extract_pagename(filename), filename])

        for dirname, _, files in self.list_dir_tree(self.current_dir+"/auto"):
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
        current_file = self.view.file_name()
        try:
            current_dir = os.path.dirname(current_file)
        except:
            current_dir = os.path.dirname(".")

        if "uruk_egypt" in current_dir and not "docs" in current_dir:
            current_dir = os.path.dirname("/Users/me/Documents/uruk_egypt/docs/")

        markdown_extension = self.view.settings().get("mde.wikilinks.markdown_extension", DEFAULT_MARKDOWN_EXTENSION)

        filename = os.path.join(current_dir, pagename + markdown_extension)

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
