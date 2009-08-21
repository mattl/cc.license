"""
Formatters take a License instance and a dictionary of work metadata about
the licensed work. The keys of this work_dict are as follows:

 - format (Audio:Sound, Video:MovingImage, Image:StillImage,
           Text:Text, Interactive:InteractiveResource)
 - worktitle
 - attribution_name
 - attribution_url
 - source_work
 - more_permissions_url
"""

import os

from chameleon.zpt.template import PageTemplateFile
from zope.i18n.translationdomain import TranslationDomain
from zope.i18n.gettextmessagecatalog import GettextMessageCatalog
from zope.i18n.interfaces import ITranslationDomain
from zope.i18n.compile import compile_mo_file
import zope.interface
from zope import component

from cc.license._lib.interfaces import ILicenseFormatter
from cc.license import util

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'templates')
BASE_TEMPLATE = os.path.join(TEMPLATE_PATH, 'base.pt')
DEFAULT_HEADER_TEMPLATE = os.path.join(TEMPLATE_PATH, 'default_header.pt')
ATTRIBUTION_HEADER_TEMPLATE = os.path.join(
    TEMPLATE_PATH, 'attribution_header.pt')
WORKTITLE_HEADER_TEMPLATE = os.path.join(TEMPLATE_PATH, 'worktitle_header.pt')
ATTRIBUTION_WORKTITLE_HEADER_TEMPLATE = os.path.join(
    TEMPLATE_PATH, 'attribution_worktitle_header.pt')

PARENT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
I18N_PATH = os.path.join(PARENT_PATH, 'i18n')

DOMAIN_SETUP = False

class HTMLFormatter(object):
    zope.interface.implements(ILicenseFormatter)

    def __repr__(self):
        return "<LicenseFormatter object '%s'>" % self.id

    def __str__(self):
        return '(%s)' % self.title

    @property
    def id(self):
        return 'html+rdfa'

    @property
    def title(self):
        return "HTML + RDFa formatter"

    def _translate_dctype(self, format):
        try:
            return {
                     None : None,
                     'audio' : 'Sound',
                     'video' : 'MovingImage',
                     'image' : 'StillImage',
                     'text' : 'Text',
                     'interactive' : 'InteractiveResource',
                   }[format]
        except KeyError: # if we dont understand it, pretend its not there
            return None

    def setup_i18n(self):
        global DOMAIN_SETUP
        if DOMAIN_SETUP:
            return

        domain = TranslationDomain('cc.license')
        for catalog in os.listdir(I18N_PATH):

            catalog_path = os.path.join(I18N_PATH, catalog)

            po_path = os.path.join(catalog_path, 'cc.license.po')
            mo_path = os.path.join(catalog_path, 'cc.license.mo')
            if not os.path.isdir(catalog_path) or not os.path.exists(po_path):
                continue

            compile_mo_file('cc.license', catalog_path)
            
            domain.addCatalog(GettextMessageCatalog(
                    catalog, 'cc.license', mo_path))

        component.provideUtility(domain, ITranslationDomain, name='cc.license')
        DOMAIN_SETUP = True

    def format(self, license, work_dict=None, locale='en', country='US'):
        """Return an HTML + RDFa string serialization for the license,
            optionally incorporating the work metadata and locale."""
        self.setup_i18n()

        work_dict = work_dict or {}

        main_text_type = 'default'
        if (work_dict.get('attribution_url')
                or work_dict.get('attribution_name')) \
                and work_dict.get('worktitle'):
            main_text_type = 'attribution_worktitle'
        elif work_dict.get('attribution_url') \
                or work_dict.get('attribution_name'):
            main_text_type = 'attribution'
        elif work_dict.get('worktitle'):
            main_text_type = 'worktitle'

        dctype = None
        if work_dict.get('format'):
            dctype = self._translate_dctype(work_dict['format'].lower())

        base_template = PageTemplateFile(BASE_TEMPLATE)
        rendered_template = base_template.render(
            main_text_type=main_text_type,
            dctype=dctype,
            this_license=license, locale=locale,
            target_language='%s_%s' % (locale, country),
            worktitle=work_dict.get('worktitle'),
            default_header=PageTemplateFile(DEFAULT_HEADER_TEMPLATE),
            attribution_header=PageTemplateFile(ATTRIBUTION_HEADER_TEMPLATE),
            worktitle_header=PageTemplateFile(WORKTITLE_HEADER_TEMPLATE),
            attribution_worktitle_header=PageTemplateFile(
                ATTRIBUTION_WORKTITLE_HEADER_TEMPLATE),
            attribution_name=(work_dict.get('attribution_name')
                              or work_dict.get('attribution_url')),
            attribution_url=work_dict.get('attribution_url'),
            source_work=work_dict.get('source_work'),
            more_permissions_url=work_dict.get('more_permissions_url'))
        return util.stripped_inner_xml(rendered_template)
