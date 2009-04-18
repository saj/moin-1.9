# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - lists of translateable strings

    MoinMoin uses some translateable strings that do not appear at other
    places in the source code (and thus, are not found by gettext when
    extracting translateable strings).
    Also, some strings need to be organized somehow.

    TODO i18n.strings / general:
    * check page lists (complete? correct?)
    * update po files on master19 wiki
    * fix "de" translation for more experiments
    * fix other translations (can be done using ##master-page, but help
      from a native speaker would be the preferred solution)
    * use pagelists here + translation from po file if there is no SystemPagesInXxGroup
      for creation of language packs (keep group pages as long as needed!)
    * delete SystemPagesInGermanGroup to try it
    * delete other SystemPagesInXXXGroup if their po file is complete

    TODO "checktranslation" plugin action for master19:
    * uses request.values.get("lang", request.user.lang or "en")
    * uses page lists to create table:
      * | OriginalPageLink (raw) | TranslatedPageLink (edit) | <update> |
      * page links make it easy to see what exists and what not
      * additionally raw and edit links are given to support c&p
      * <update> can indicate an update need for the translation
    * list pages on master19 that are not referenced by any original or
      translated page name (in any supported language)

    @copyright: 2009 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

_ = lambda x: x # dummy translation function

# Some basic pages used for every language, but we only need them once in English (don't translate!):
not_translated_system_pages = [
    _('SystemPagesSetup'),
    _('InterWikiMap'),
    _('BadContent'),
    _('LocalBadContent'),
    _('EditedSystemPages'),
    _('LocalSpellingWords'),
    _('SystemAdmin'),
    _('ProjectTemplate'),
    _('ProjectGroupsTemplate'),
]

essential_system_pages = [
    _('RecentChanges'),
    _('WikiTipOfTheDay'), # used by RecentChanges
    _('TitleIndex'),
    _('WordIndex'),
    _('FindPage'),
    _('MissingPage'),
    _('MissingHomePage'),
    _('PermissionDeniedPage'),
    _('SystemInfo'),
    _('WikiHomePage'), # used by ...?
]

optional_system_pages = [
    _('FrontPage'),
    _('WikiSandBox'),
    _('InterWiki'),
    _('WikiLicense'),
    _('AbandonedPages'),
    _('OrphanedPages'),
    _('WantedPages'),
    _('EventStats'),
    _('EventStats/HitCounts'),
    _('EventStats/Languages'),
    _('EventStats/UserAgents'),
    _('PageSize'),
    _('PageHits'),
    _('RandomPage'),
    _('XsltVersion'),
    _('FortuneCookies'), # use by RandomQuote macro
]

translated_system_pages = essential_system_pages + optional_system_pages

all_system_pages = not_translated_system_pages + translated_system_pages

essential_category_pages = [
    _('CategoryCategory'),
    _('CategoryHomepage'),
]

optional_category_pages = [
]

all_category_pages = essential_category_pages + optional_category_pages

essential_template_pages = [
    _('CategoryTemplate'),
    _('HomepageTemplate'),
]

optional_template_pages = [
    _('HelpTemplate'),
    _('HomepageReadWritePageTemplate'),
    _('HomepageReadPageTemplate'),
    _('HomepagePrivatePageTemplate'),
    _('HomepageGroupsTemplate'),
    _('SlideShowHandOutTemplate'),
    _('SlideShowTemplate'),
    _('SlideTemplate'),
    _('SyncJobTemplate'),
]

all_template_pages = essential_template_pages + optional_template_pages

# Installation / Configuration / Administration Help:
admin_pages = [
    _('HelpOnConfiguration'),
    _('HelpOnConfiguration/EmailSupport'),
    _('HelpOnConfiguration/SecurityPolicy'),
    _('HelpOnConfiguration/FileAttachments'),
    _('HelpOnConfiguration/SupplementationPage'),
    _('HelpOnConfiguration/SurgeProtection'),
    _('HelpOnConfiguration/UserPreferences'),
    _('HelpOnPackageInstaller'),
    _('HelpOnUpdating'),
    _('HelpOnUpdatingPython'),
    _('HelpOnAdministration'),
    _('HelpOnAuthentication'),
    _('HelpOnAuthentication/ExternalCookie'),
    _('HelpOnMoinCommand'),
    _('HelpOnMoinCommand/ExportDump'),
    _('HelpOnNotification'),
    _('HelpOnSessions'),
    _('HelpOnUserHandling'),
    _('HelpOnXapian'),
]

# Stuff that should live on moinmo.in wiki:
obsolete_pages = [
    _('HelpMiscellaneous'),
    _('HelpMiscellaneous/FrequentlyAskedQuestions'),
    _('WikiWikiWeb'),
    _('CamelCase'),
    _('WikiName'),
]

essential_help_pages = [
    _('HelpOnMoinWikiSyntax'), # used by edit action
    _('HelpOnCreoleSyntax'), # used by edit action
]

optional_help_pages = [
    _('HelpOnFormatting'), # still needed?
    _('MoinMoin'),
    _('HelpContents'),
    _('HelpForBeginners'),
    _('HelpForUsers'),
    _('HelpIndex'),
    _('HelpOnAccessControlLists'),
    _('HelpOnAcl'),
    _('HelpOnActions'),
    _('HelpOnActions/AttachFile'),
    _('HelpOnAdmonitions'),
    _('HelpOnAutoAdmin'),
    _('HelpOnCategories'),
    _('HelpOnDictionaries'),
    _('HelpOnEditLocks'),
    _('HelpOnEditing'), # used by edit action!
    _('HelpOnEditing/SubPages'),
    _('HelpOnGraphicalEditor'),
    _('HelpOnHeadlines'),
    _('HelpOnLanguages'),
    _('HelpOnLinking'),
    _('HelpOnLinking/NotesLinks'),
    _('HelpOnLists'),
    _('HelpOnLogin'),
    _('HelpOnMacros'),
    _('HelpOnMacros/EmbedObject'),
    _('HelpOnMacros/ImageLink'),
    _('HelpOnMacros/Include'),
    _('HelpOnMacros/MailTo'),
    _('HelpOnMacros/MonthCalendar'),
    _('HelpOnNavigation'),
    _('HelpOnOpenIDProvider'),
    _('HelpOnPageCreation'),
    _('HelpOnPageDeletion'),
    _('HelpOnParsers'),
    _('HelpOnParsers/ReStructuredText'),
    _('HelpOnParsers/ReStructuredText/RstPrimer'),
    _('HelpOnProcessingInstructions'),
    _('HelpOnRules'),
    _('HelpOnSearching'),
    _('HelpOnSlideShows'),
    _('HelpOnSlideShows/000 Introduction'),
    _('HelpOnSlideShows/100 Creating the slides'),
    _('HelpOnSlideShows/900 Last but not least: Running your presentation'),
    _('HelpOnSmileys'),
    _('HelpOnSpam '),
    _('HelpOnSpellCheck'),
    _('HelpOnSuperUser'),
    _('HelpOnSynchronisation'),
    _('HelpOnTables'),
    _('HelpOnTemplates'),
    _('HelpOnThemes'),
    _('HelpOnUserPreferences'),
    _('HelpOnVariables'),
    _('HelpOnXmlPages'),
    _('HelpOnComments'),
    _('HelpOnSubscribing'),
]

all_help_pages = essential_help_pages + optional_help_pages

# Wiki Course:
course_pages = [
    _('WikiCourse'),
    _('WikiCourse/01 What is a MoinMoin wiki?'),
    _('WikiCourse/02 Finding information'),
    _('WikiCourse/03 Staying up to date'),
    _('WikiCourse/04 Creating a wiki account'),
    _('WikiCourse/05 User preferences'),
    _('WikiCourse/06 Your own wiki homepage'),
    _('WikiCourse/07 The text editor'),
    _('WikiCourse/08 Hot Keys'),
    _('WikiCourse/10 Text layout with wiki markup'),
    _('WikiCourse/11 Paragraphs'),
    _('WikiCourse/12 Headlines'),
    _('WikiCourse/13 Lists'),
    _('WikiCourse/14 Text styles'),
    _('WikiCourse/15 Tables'),
    _('WikiCourse/16 Wiki internal links'),
    _('WikiCourse/17 External links'),
    _('WikiCourse/18 Attachments'),
    _('WikiCourse/19 Symbols'),
    _('WikiCourse/20 Dynamic content'),
    _('WikiCourse/21 Macros'),
    _('WikiCourse/22 Parsers'),
    _('WikiCourse/23 Actions'),
    _('WikiCourse/30 The graphical editor'),
    _('WikiCourse/40 Creating more pages'),
    _('WikiCourse/50 Wiki etiquette'),
    _('WikiCourse/51 Applications'),
    _('WikiCourse/52 Structure in the wiki'),
    _('WikiCourseHandOut'),
]

all_essential_pages = (
    essential_system_pages +
    essential_category_pages +
    essential_template_pages +
    essential_help_pages
)

all_pages = (
    all_system_pages +
    all_category_pages +
    all_template_pages +
    all_help_pages +
    admin_pages +
    obsolete_pages +
    course_pages
)

# we use Sun at index 0 and 7 to be compatible with EU and US day indexing
# schemes, like it is also done within crontab entries:
weekdays = [_('Sun'), _('Mon'), _('Tue'), _('Wed'), _('Thu'), _('Fri'), _('Sat'), _('Sun')]

actions = [
    _('AttachFile'),
    _('DeletePage'),
    _('LikePages'),
    _('LocalSiteMap'),
    _('RenamePage'),
    _('SpellCheck'),
]

misc = [
    # the editbar link text of the default supplementation page link:
    _('Discussion'),
]

del _ # delete the dummy translation function

