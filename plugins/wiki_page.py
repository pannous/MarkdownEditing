import os
import string
import sys

import sublime

from datetime import date

from .logging import logger
from .view import MdeTextCommand
from ..wiki_page import WikiPage

DEFAULT_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_HOME_PAGE = "HomePage"


class MdeListBackLinksCommand(MdeTextCommand):
    def run(self, edit):
        wiki_page = WikiPage(self.view)

        file_list = wiki_page.find_files_with_ref()
        wiki_page.select_backlink(file_list)


class MdeMakePageReferenceCommand(MdeTextCommand):
    def is_visible(self):
        """Return True if  is on a wiki page reference."""
        if not super().is_visible():
            return False
        for sel in self.view.sel():
            if self.view.match_selector(sel.begin(), "meta.link.reference.wiki"):
                return False
        return True

    def run(self, edit):
        wiki_page = WikiPage(self.view)

        word_region = wiki_page.select_word_at_cursor()
        file_list = wiki_page.find_matching_files(word_region)

        wiki_page.make_page_reference(edit, word_region)

        if len(file_list) > 1:
            wiki_page.show_quick_list(file_list)


class MdeOpenHomePageCommand(MdeTextCommand):
    def run(self, edit):
        home_page = self.view.settings().get("mde.wikilinks.homepage", DEFAULT_HOME_PAGE)

        wiki_page = WikiPage(self.view)
        wiki_page.select_page(home_page)


class MdeOpenJournalCommand(MdeTextCommand):
    def run(self, edit):
        today = date.today()
        date_format = self.view.settings().get("mde.journal.dateformat", DEFAULT_DATE_FORMAT)
        name = today.strftime(date_format)

        wiki_page = WikiPage(self.view)
        wiki_page.select_page(name)


class MdeOpenPageCommand(MdeTextCommand):
    def is_visible(self):
        """Return True if caret is on a wiki page reference."""
        for sel in self.view.sel():
            if self.view.match_selector(sel.begin(), "meta.link.reference.wiki"):
                return True
        return False

    def run(self, edit):
        wiki_page = WikiPage(self.view)

        sel_region = self.get_selected()
        if sel_region:
            wiki_page.select_word_at_cursor()

            region = sublime.Region(sel_region.begin(), sel_region.begin())
            file_list = wiki_page.find_matching_files(region)

            if len(file_list) > 1:
                wiki_page.show_quick_list(file_list)
        else:
            name = wiki_page.identify_page_at_cursor()
            wiki_page.select_page(name)

    def get_selected(self):
        selection = self.view.sel()
        for region in selection:
            return region

        return None


class MdePrepareFromTemplateCommand(MdeTextCommand):

    DEFAULT_PAGE_TEMPLATE = "templates/PageTemplate.md"
    PRESET_TEMPLATE_TEXT = "# $title\n\n"

    def run(self, edit, **args):
        """Prepare a new page content from a named template.

        :Example:

        view.run_command('mde_prepare_from_template', {
            'title': pagename,
            'template': 'default_page'
        })

        :param self: This command instance
        :param edit: The sublime edit instance
        :param args: The command arguments including 'title' and 'template'
        """

        template_name = args["template"]
        logger.info("Creating new page from template: ", template_name)

        text = self.generate_from_template(template_name, args)
        self.view.insert(edit, 0, text)

    def generate_from_template(self, template_name, args):
        """Generate the text using the template"""

        template_text = self.retrieve_template_text(template_name)
        template = string.Template(template_text)
        return template.substitute(args)

    def retrieve_template_text(self, template_name):
        """Retrieve the template text.

        The setting 'mde.wikilinks.templates' may be configured with a filename for
        the template.  This file (if it exists) will be loaded otherwise the preset
        template will be used
        """

        template = self.view.settings().get("mde.wikilinks.templates", self.DEFAULT_PAGE_TEMPLATE)

        if not os.path.isfile(template):
            current_file = self.view.file_name()
            current_dir = os.path.dirname(current_file)
            template = os.path.join(current_dir, template)

        if os.path.isfile(template):
            logger.debug("Using template:", template)
            try:
                with open(template, "rt") as f:
                    return f.read()
            except OSError:
                logger.debug("Unable to read template:", sys.exc_info()[0])

        # Unable to load template  so using preset template
        logger.warning("Template:", template, "not found. Using preset.")
        return self.PRESET_TEMPLATE_TEXT
