#!/usr/bin/env python2.4
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - internationalization (aka i18n)

    We use Python's gettext module now for loading <language>.<domain>.mo files.
    Domain is "MoinMoin" for MoinMoin distribution code and something else for
    extension translations.

    Public attributes:
        languages -- dict of languages that MoinMoin knows metadata about

    Public functions:
        requestLanguage(request, usecache=1) -- return the request language
        wikiLanguages() -- return the available wiki user languages
        browserLanguages() -- return the browser accepted languages
        getDirection(lang) -- return the lang direction either 'ltr' or 'rtl'
        getText(str, request) -- return str translation

    TODO: as soon as we have some "farm / server plugin dir", extend this to
          load translations from there, too.

    @copyright: 2001-2004 Juergen Hermann <jh@web.de>,
                2005-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
debug = 0

import os, gettext, glob

from MoinMoin import caching

# This is a global for a reason: in persistent environments all languages in
# use will be cached; Note: you have to restart if you update language data.

# key: language, value: language metadata
# this gets loaded early and completely:
languages = None

translations = {}

def po_filename(request, language, domain):
    """ we use MoinMoin/i18n/<language>[.<domain>].mo as filename for the PO file.

        TODO: later, when we have a farm scope plugin dir, we can also load
              language data from there.
    """
    return os.path.join(request.cfg.moinmoin_dir, 'i18n', "%s.%s.po" % (language, domain))

def i18n_init(request):
    """ this is called early from request initialization and makes sure we
        have metadata (like what languages are available, direction of language)
        loaded into the global "languages".
        The very first time, this will be slow as it will load all languages,
        but next time it will be fast due to caching.
    """
    global languages
    request.clock.start('i18n_init')
    if languages is None:
        meta_cache = caching.CacheEntry(request, 'i18n', 'meta', scope='farm', use_pickle=True)
        i18n_dir = os.path.join(request.cfg.moinmoin_dir, 'i18n')
        if meta_cache.needsUpdate(i18n_dir):
            _languages = {}
            for lang_file in glob.glob(po_filename(request, language='*', domain='MoinMoin')): # XXX only MoinMoin domain for now
                language, domain, ext = os.path.basename(lang_file).split('.')
                t = Translation(language, domain)
                f = file(lang_file)
                t.load_po(f)
                f.close()
                #request.log("load translation %r" % language)
                encoding = 'utf-8'
                _languages[language] = {}
                for key, value in t.info.items():
                    #request.log("meta key %s value %r" % (key, value))
                    _languages[language][key] = value.decode(encoding)
            try:
                meta_cache.update(_languages)
            except caching.CacheError:
                pass

        if languages is None: # another thread maybe has done it before us
            try:
                _languages = meta_cache.content()
                if languages is None:
                    languages = _languages
            except caching.CacheError:
                pass
    request.clock.stop('i18n_init')


class Translation(object):
    """ This class represents a translation. Usually this is a translation
        from English original texts to a single language, like e.g. "de" (german).

        The domain value defaults to 'MoinMoin' and this is reserved for
        translation of the MoinMoin distribution. If you do a translation for
        a third-party plugin, you have to use a different and unique value.
    """
    def __init__(self, language, domain='MoinMoin'):
        self.language = language
        self.domain = domain

    def load_po(self, f):
        """ load the po file """
        from StringIO import StringIO
        from MoinMoin.i18n.msgfmt import MsgFmt
        mf = MsgFmt()
        mf.read_po(f.readlines())
        mo_data = mf.generate_mo()
        f = StringIO(mo_data)
        self.load_mo(f)
        f.close()

    def load_mo(self, f):
        """ load the mo file, setup some attributes from metadata """
        # binary files have to be opened in the binary file mode!
        self.translation = gettext.GNUTranslations(f)
        self.info = info = self.translation.info()
        self.name = info['x-language']
        self.ename = info['x-language-in-english']
        self.direction = info['x-direction']
        assert self.direction in ('ltr', 'rtl', )
        self.maintainer = info['last-translator']

    def formatMarkup(self, request, text, currentStack=[]):
        """
        Formats the text passed according to wiki markup.
        This raises an exception if a text needs itself to be translated,
        this could possibly happen with macros.
        """
        try:
            currentStack.index(text)
            raise Exception("Formatting a text that is being formatted?!")
        except ValueError:
            pass
        currentStack.append(text)

        from MoinMoin.Page import Page
        from MoinMoin.parser.text_moin_wiki import Parser as WikiParser
        from MoinMoin.formatter.text_html import Formatter
        import StringIO

        out = StringIO.StringIO()
        request.redirect(out)
        parser = WikiParser(text, request, line_anchors=False)
        formatter = Formatter(request, terse=True)
        reqformatter = None
        if hasattr(request, 'formatter'):
            reqformatter = request.formatter
        request.formatter = formatter
        p = Page(request, "$$$$i18n$$$$")
        formatter.setPage(p)
        parser.format(formatter)
        text = out.getvalue()
        if reqformatter is None:
            del request.formatter
        else:
            request.formatter = reqformatter
        request.redirect()
        del currentStack[-1]
        text = text.strip()
        return text

    def loadLanguage(self, request):
        request.clock.start('loadLanguage')
        cache = caching.CacheEntry(request, arena='i18n', key=self.language, scope='farm', use_pickle=True)
        langfilename = po_filename(request, self.language, self.domain)
        needsupdate = cache.needsUpdate(langfilename)
        if debug:
            request.log("i18n: langfilename %s needsupdate %d" % (langfilename, needsupdate))
        if not needsupdate:
            try:
                uc_texts, uc_unformatted = cache.content()
            except caching.CacheError:
                if debug:
                    request.log("i18n: pickle %s load failed" % self.language)
                needsupdate = 1

        if needsupdate:
            f = file(langfilename)
            self.load_po(f)
            f.close()
            trans = self.translation
            texts = trans._catalog
            has_wikimarkup = self.info.get('x-haswikimarkup', 'False') == 'True'
            # convert to unicode
            if debug:
                request.log("i18n: processing unformatted texts of lang %s" % self.language)
            uc_unformatted = {}
            uc_texts = {}
            for ukey, utext in texts.items():
                uc_unformatted[ukey] = utext
                if has_wikimarkup:
                    # use the wiki parser now to replace some wiki markup with html
                    try:
                        uc_texts[ukey] = self.formatMarkup(request, utext) # XXX RECURSION!!! Calls gettext via markup
                    except: # infinite recursion or crash
                        if debug:
                            request.log("i18n: crashes in language %s on string: %s" % (self.language, utext))
                        uc_texts[ukey] = u"%s*" % utext
            if debug:
                request.log("i18n: dumping lang %s" % self.language)
            try:
                cache.update((uc_texts, uc_unformatted))
            except caching.CacheError:
                pass

        self.formatted = uc_texts
        self.raw = uc_unformatted
        request.clock.stop('loadLanguage')


def getDirection(lang):
    """ Return the text direction for a language, either 'ltr' or 'rtl'. """
    return languages[lang]['x-direction']

def getText(original, request, lang, formatted=True):
    """ Return a translation of text in the user's language. """
    if original == u"":
        return u"" # we don't want to get *.po files metadata!

    global translations
    if not lang in translations: # load translation if needed
        t = Translation(lang)
        t.loadLanguage(request)
        translations[lang] = t

    # get the matching entry in the mapping table
    translated = original
    if formatted:
        trans_table = translations[lang].formatted
    else:
        trans_table = translations[lang].raw
    try:
        translated = trans_table[original]
    except KeyError:
        try:
            language = languages[lang]['x-language-in-english']
            dictpagename = "%sDict" % language
            dicts = request.dicts
            if dicts.has_dict(dictpagename):
                userdict = dicts.dict(dictpagename)
                translated = userdict[original]
            else:
                raise KeyError
        except KeyError:
            # do not simply return trans with str, but recursively call
            # to get english translation, maybe formatted.
            # if we don't find an english "translation", we just format it
            # on the fly (this is needed for cfg.editor_quickhelp).
            if lang != 'en':
                translated = getText(original, request, 'en', formatted)
            elif formatted:
                translated = translations[lang].formatMarkup(request, original)
    return translated


def requestLanguage(request, try_user=True):
    """
    Return the user interface language for this request.

    The user interface language is taken from the user preferences for
    registered users, or request environment, or the default language of
    the wiki, or English.

    This should be called once per request, then you should get the value from
    request object lang attribute.

    Unclear what this means: "Until the code for get
    text is fixed, we are caching the request language locally."

    @param request: the request object
    @param try_user: try getting language from request.user
    @keyword usecache: whether to get the value form the local cache or
                       actually look for it. This will update the cache data.
    @rtype: string
    @return: ISO language code, e.g. 'en'
    """
    # Return the user language preferences for registered users
    if try_user and request.user.valid and request.user.language:
        return request.user.language

    # Or try to return one of the user browser accepted languages, if it
    # is available on this wiki...
    available = wikiLanguages()
    if not request.cfg.language_ignore_browser:
        for lang in browserLanguages(request):
            if lang in available:
                return lang

    # Or return the wiki default language...
    if request.cfg.language_default in available:
        lang = request.cfg.language_default
    # If everything else fails, read the manual... or return 'en'
    else:
        lang = 'en'
    return lang

def wikiLanguages():
    """
    Return the available user languages in this wiki.
    As we do everything in unicode (or utf-8) now, everything is available.
    """
    return languages

def browserLanguages(request):
    """
    Return the accepted languages as set in the user browser.

    Parse the HTTP headers and extract the accepted languages, according to:
    http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.4

    Return a list of languages and base languages - as they are specified in
    the request, normalizing to lower case.
    """
    fallback = []
    accepted = request.http_accept_language
    if accepted:
        # Extract the languages names from the string
        accepted = accepted.split(',')
        accepted = [lang.split(';')[0] for lang in accepted]
        # Add base language for each sub language. If the user specified
        # a sub language like "en-us", we will try to to provide it or
        # a least the base language "en" in this case.
        for lang in accepted:
            lang = lang.lower()
            fallback.append(lang)
            if '-' in lang:
                baselang = lang.split('-')[0]
                fallback.append(baselang)
    return fallback

