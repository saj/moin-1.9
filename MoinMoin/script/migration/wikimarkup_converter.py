#!/usr/bin/env python

import re
from MoinMoin import config, wikiutil, macro

class Parser:
    PARENT_PREFIX = wikiutil.PARENT_PREFIX
    # quoted strings (we require that there is at least one char (that is not the quoting char)
    # inside to not confuse stuff like '''Contact:''' (just a bold Contact:) with interwiki markup
    # OtherWiki:'Page with blanks'
    sq_string = ur"('[^']+?')" # single quoted string
    dq_string = ur"(\"[^\"]+?\")" # double quoted string
    q_string = ur"(%s|%s)" % (sq_string, dq_string) # quoted string
    attachment_schemas = ["attachment", "inline", "drawing"]
    punct_pattern = re.escape(u'''"\'}]|:,.)?!''')
    punct_no_quote_pattern = re.escape(u'''}]|:,.)?!''')
    url_pattern = (u'http|https|ftp|nntp|news|mailto|telnet|wiki|file|irc|' +
            u'|'.join(attachment_schemas) +
            (config.url_schemas and u'|' + u'|'.join(config.url_schemas) or ''))
    word_rule = ur'(?:(?<![%(u)s%(l)s])|^)%(parent)s(?:%(subpages)s(?:[%(u)s][%(l)s]+){2,})+(?![%(u)s%(l)s]+)' % {
        'u': config.chars_upper,
        'l': config.chars_lower,
        'subpages': wikiutil.CHILD_PREFIX + '?',
        'parent': ur'(?:%s)?' % re.escape(PARENT_PREFIX),
    }
    url_rule = ur'%(url_guard)s(%(url)s)\:(([^\s\<%(punct)s]|([%(punctnq)s][^\s\<%(punct)s]))+|%(q_string)s)' % {
        'url_guard': ur'(^|(?<!\w))',
        'url': url_pattern,
        'punct': punct_pattern,
        'punctnq': punct_no_quote_pattern,
        'q_string': q_string,
    }
    ol_rule = ur"^\s+(?:[0-9]+|[aAiI])\.(?:#\d+)?\s"
    dl_rule = ur"^\s+.*?::\s"
    pre_formatting_rules = ur"""(?P<pre>(\}\}\}))"""

    formatting_rules = ur"""(?P<ent_numeric>&#(\d{1,5}|x[0-9a-fA-F]+);)
(?:(?P<emph_ibb>'''''(?=[^']+'''))
(?P<emph_ibi>'''''(?=[^']+''))
(?P<emph_ib_or_bi>'{5}(?=[^']))
(?P<emph>'{2,3})
(?P<u>__)
(?P<sup>\^.*?\^)
(?P<sub>,,[^,]{1,40},,)
(?P<tt>\{\{\{.*?\}\}\})
(?P<parser>(\{\{\{(#!.*|\s*$)))
(?P<pre>(\{\{\{ ?|\}\}\}))
(?P<small>(\~- ?|-\~))
(?P<big>(\~\+ ?|\+\~))
(?P<strike>(--\(|\)--))
(?P<rule>-{4,})
(?P<comment>^\#\#.*$)
(?P<macro>\[\[(%%(macronames)s)(?:\(.*?\))?\]\]))
(?P<ol>%(ol_rule)s)
(?P<dl>%(dl_rule)s)
(?P<li>^\s+\*\s*)
(?P<li_none>^\s+\.\s*)
(?P<indent>^\s+)
(?P<tableZ>\|\| $)
(?P<table>(?:\|\|)+(?:<[^>]*?>)?(?!\|? $))
(?P<heading>^\s*(?P<hmarker>=+)\s.*\s(?P=hmarker) $)
(?P<interwiki>[A-Z][a-zA-Z]+\:(%(q_string)s|([^\s'\"\:\<\|]([^\s%(punct)s]|([%(punct)s][^\s%(punct)s]))+)))
(?P<word>%(word_rule)s)
(?P<url_bracket>\[((%(url)s)\:|#|\:)[^\s\]]+(\s[^\]]+)?\])
(?P<url>%(url_rule)s)
(?P<email>[-\w._+]+\@[\w-]+(\.[\w-]+)+)
(?P<smiley>(?<=\s)(%(smiley)s)(?=\s))
(?P<smileyA>^(%(smiley)s)(?=\s))
(?P<ent_symbolic>&[a-zA-Z]+;)
(?P<ent>[<>&])
(?P<wikiname_bracket>\[%(q_string)s.*?\])
(?P<tt_bt>`.*?`)"""  % {

        'url': url_pattern,
        'punct': punct_pattern,
        'q_string': q_string,
        'ol_rule': ol_rule,
        'dl_rule': dl_rule,
        'url_rule': url_rule,
        'word_rule': word_rule,
        'smiley': u'|'.join(map(re.escape, config.smileys))}

    def __init__(self, raw, request, **kw):
        self.raw = raw
        self.request = request
        self._ = request.getText
        self.cfg = request.cfg

        self.is_em = 0 # must be int!
        self.is_b = 0 # must be int!
        self.is_u = False
        self.is_strike = False
        self.is_big = False
        self.is_small = False

        self.in_list = 0 # between <ul/ol/dl> and </ul/ol/dl>
        self.in_li = 0 # between <li> and </li>
        self.in_dd = 0 # between <dd> and </dd>

        self.in_table = 0

        # states of the parser concerning being inside/outside of some "pre" section:
        # None == we are not in any kind of pre section (was: 0)
        # 'search_parser' == we didn't get a parser yet, still searching for it (was: 1)
        # 'found_parser' == we found a valid parser (was: 2)
        # 'no_parser' == we have no (valid) parser, use a normal <pre>...</pre> (was: 3)
        self.in_pre = None

        # holds the nesting level (in chars) of open lists
        self.list_indents = []
        self.list_types = []

        self.formatting_rules = self.formatting_rules % {'macronames': u'|'.join(macro.getNames(self.cfg))}

    def _emph_repl(self, word):
        if len(word) == 3:
            self.is_b = not self.is_b
            if self.is_em and self.is_b:
                self.is_b = 2
            if self.is_b:
                return "'''"
            else:
                return "'''"
        else: # 2
            self.is_em = not self.is_em
            if self.is_em and self.is_b:
                self.is_em = 2
            if self.is_em:
                return "''"
            else:
                return "''"

    def _emph_ibb_repl(self, word):
        self.is_b = not self.is_b
        self.is_em = not self.is_em
        if self.is_em and self.is_b:
            self.is_b = 2
        return "'''''" # make more precise when needed

    def _emph_ibi_repl(self, word):
        self.is_b = not self.is_b
        self.is_em = not self.is_em
        if self.is_em and self.is_b:
            self.is_em = 2
        return "'''''" # make more precise when needed

    def _emph_ib_or_bi_repl(self, word):
        b_before_em = self.is_b > self.is_em > 0
        self.is_b = not self.is_b
        self.is_em = not self.is_em
        if b_before_em:
            return "'''''" # b em
        else:
            return "'''''" # em b

    def _u_repl(self, word):
        self.is_u = not self.is_u
        if self.is_u:
            return "__"
        else:
            return "__"

    def _strike_repl(self, word):
        self.is_strike = not self.is_strike
        if self.is_strike:
            return "--("
        else:
            return ")--"

    def _sup_repl(self, word):
        return "^%s^" % word[1:-1]

    def _sub_repl(self, word):
        return ",,%s,," % word[2:-2]

    def _small_repl(self, word):
        if word.strip() == '~-' and self.is_small:
            return word
        if word.strip() == '-~' and not self.is_small:
            return word
        self.is_small = not self.is_small
        if self.is_small:
            return "~-"
        else:
            return "-~"

    def _big_repl(self, word):
        if word.strip() == '~+' and self.is_big:
            return word
        if word.strip() == '+~' and not self.is_big:
            return word
        self.is_big = not self.is_big
        if self.is_big:
            return "~+"
        else:
            return "+~"

    def _tt_repl(self, word):
        return "{{{%s}}}@ % word[3:-3]

    def _tt_bt_repl(self, word):
        return "`%s`" % word[1:-1]

    def _notword_repl(self, word):
        return "!%s" % word[1:]

    def _rule_repl(self, word):
        return word # make more precise when needed

    def _smiley_repl(self, word):
        return word
    _smileyA_repl = _smiley_repl

    def _ent_repl(self, word):
        """Handle SGML entities."""
        return word

    def _ent_numeric_repl(self, word):
        """Handle numeric (decimal and hexadecimal) SGML entities."""
        return word

    def _ent_symbolic_repl(self, word):
        """Handle symbolic SGML entities."""
        return word

    def _comment_repl(self, word):
        self.line_is_empty = 1 # markup following comment lines treats them as if they were empty
        return word

    def _macro_repl(self, word):
        macro_name = word[2:-2]
        # check for arguments
        args = None
        if macro_name.count("("):
            macro_name, args = macro_name.split('(', 1)
            args = args[:-1]
        if args:
            return "[[%s(%s)]]" % (macro_name, args)
        else:
            return "[[%s]]" % macro_name

    def _pre_repl(self, word):
        word = word.strip()
        if word == '{{{' and not self.in_pre:
            self.in_pre = 'no_parser'
            return "{{{"
        elif word == '}}}' and self.in_pre:
            self.in_pre = None
            return "}}}"
        return word

    def _parser_repl(self, word):
        if word.startswith('{{{'):
            word = word[3:]

        self.parser = None
        self.parser_name = None
        s_word = word.strip()
        if s_word == '#!':
            # empty bang paths lead to a normal code display
            # can be used to escape real, non-empty bang paths
            word = ''
            self.in_pre = 'no_parser'
            return "{{{"
        elif s_word.startswith('#!'):
            # First try to find a parser for this
            parser_name = s_word[2:].split()[0]  # XXX loses args
            self.setParser(parser_name)

        if self.parser:
            self.parser_name = parser_name
            self.in_pre = 'found_parser'
            self.parser_lines = [word]
            return ''
        elif s_word:
            self.in_pre = 'no_parser'
            return "{{{%s" % s_word
        else:
            self.in_pre = 'search_parser'
            return ''

    def _heading_repl(self, word):
        h = word.strip() # XXX loses indentation
        level = 1
        while h[level:level+1] == '=':
            level += 1
        depth = min(5, level)

        # this is needed for Included pages
        # TODO but it might still result in unpredictable results
        # when included the same page multiple times
        title_text = h[level:-level].strip()
        pntt = self.formatter.page.page_name + title_text

        h = "=" * depth
        return "%s %s %s" % (h, title_text, h)

    def _email_repl(self, word):
        return word


    # LINKS ------------------------------------------------------------------
    
    def interwiki(self, target_and_text, **kw):
        # TODO: maybe support [wiki:Page http://wherever/image.png] ?
        scheme, rest = target_and_text.split(':', 1)
        wikiname, pagename, text = wikiutil.split_wiki(rest)
        if not text:
            text = pagename
        #self.request.log("interwiki: split_wiki -> %s.%s.%s" % (wikiname,pagename,text))

        if wikiname.lower() == 'self': # [wiki:Self:LocalPage text] or [:LocalPage:text]
            return self._word_repl(pagename, text)

        # check for image URL, and possibly return IMG tag
        if not kw.get('pretty_url', 0) and wikiutil.isPicture(pagename):
            dummy, wikiurl, dummy, wikitag_bad = wikiutil.resolve_wiki(self.request, rest)
            href = wikiutil.join_wiki(wikiurl, pagename)
            #self.request.log("interwiki: join_wiki -> %s.%s.%s" % (wikiurl,pagename,href))
            return self.formatter.image(src=href)

        return (self.formatter.interwikilink(1, wikiname, pagename) +
                self.formatter.text(text) +
                self.formatter.interwikilink(0, wikiname, pagename))

    def attachment(self, target_and_text, **kw):
        """ This gets called on attachment URLs """
        _ = self._
        #self.request.log("attachment: target_and_text %s" % target_and_text)
        scheme, fname, text = wikiutil.split_wiki(target_and_text)
        if not text:
            text = fname

        if scheme == 'drawing':
            return self.formatter.attachment_drawing(fname, text)

        # check for image, and possibly return IMG tag (images are always inlined)
        if not kw.get('pretty_url', 0) and wikiutil.isPicture(fname):
            return self.formatter.attachment_image(fname)

        # inline the attachment
        if scheme == 'inline':
            return self.formatter.attachment_inlined(fname, text)

        return self.formatter.attachment_link(fname, text)


    def _interwiki_repl(self, word):
        """Handle InterWiki links."""
        wikitag, wikiurl, wikitail, wikitag_bad = wikiutil.resolve_wiki(self.request, word)
        if wikitag_bad:
            return self.formatter.text(word)
        else:
            return self.interwiki("wiki:" + word)

    def _url_repl(self, word):
        """Handle literal URLs including inline images."""
        scheme = word.split(":", 1)[0]

        if scheme == "wiki":
            return self.interwiki(word)

        if scheme in self.attachment_schemas:
            return self.attachment(word)

        if wikiutil.isPicture(word):
            word = wikiutil.mapURL(self.request, word)
            # Get image name http://here.com/dir/image.gif -> image
            name = word.split('/')[-1]
            name = ''.join(name.split('.')[:-1])
            return self.formatter.image(src=word, alt=name)
        else:
            return (self.formatter.url(1, word, css=scheme) +
                    self.formatter.text(word) +
                    self.formatter.url(0))


    def _word_repl(self, word, text=None):
        """Handle WikiNames."""

        # check for parent links
        # !!! should use wikiutil.AbsPageName here, but setting `text`
        # correctly prevents us from doing this for now
        if word.startswith(wikiutil.PARENT_PREFIX):
            if not text:
                text = word
            word = '/'.join(filter(None, self.formatter.page.page_name.split('/')[:-1] + [word[wikiutil.PARENT_PREFIX_LEN:]]))

        if not text:
            # if a simple, self-referencing link, emit it as plain text
            if word == self.formatter.page.page_name:
                return self.formatter.text(word)
            text = word
        if word.startswith(wikiutil.CHILD_PREFIX):
            word = self.formatter.page.page_name + '/' + word[wikiutil.CHILD_PREFIX_LEN:]

        # handle anchors
        parts = word.split("#", 1)
        anchor = ""
        if len(parts) == 2:
            word, anchor = parts

        return (self.formatter.pagelink(1, word, anchor=anchor) +
                self.formatter.text(text) +
                self.formatter.pagelink(0, word))

    def _wikiname_bracket_repl(self, text):
        """Handle special-char wikinames with link text, like:
           ["Jim O'Brian" Jim's home page] or ['Hello "world"!' a page with doublequotes]i
        """
        word = text[1:-1] # strip brackets
        first_char = word[0]
        if first_char in wikiutil.QUOTE_CHARS:
            # split on closing quote
            target, linktext = word[1:].split(first_char, 1)
        else: # not quoted
            # split on whitespace
            target, linktext = word.split(None, 1)
        if target:
            linktext = linktext.strip()
            return self._word_repl(target, linktext)
        else:
            return self.formatter.text(text)


    def _url_bracket_repl(self, word):
        """Handle bracketed URLs."""
        word = word[1:-1] # strip brackets

        # Local extended link? [:page name:link text] XXX DEPRECATED
        if word[0] == ':':
            words = word[1:].split(':', 1)
            if len(words) == 1:
                words = words * 2
            target_and_text = 'wiki:Self:%s %s' % (wikiutil.quoteName(words[0]), words[1])
            return self.interwiki(target_and_text, pretty_url=1)

        scheme_and_rest = word.split(":", 1)
        if len(scheme_and_rest) == 1: # no scheme
            # Traditional split on space
            words = word.split(None, 1)
            if len(words) == 1:
                words = words * 2

            if words[0].startswith('#'): # anchor link
                return (self.formatter.url(1, words[0]) +
                        self.formatter.text(words[1]) +
                        self.formatter.url(0))
        else:
            scheme, rest = scheme_and_rest
            if scheme == "wiki":
                return self.interwiki(word, pretty_url=1)
            if scheme in self.attachment_schemas:
                return self.attachment(word, pretty_url=1)

            words = word.split(None, 1)
            if len(words) == 1:
                words = words * 2

        if wikiutil.isPicture(words[1]) and re.match(self.url_rule, words[1]):
            return (self.formatter.url(1, words[0], css='external', do_escape=0) +
                    self.formatter.image(title=words[0], alt=words[0], src=words[1]) +
                    self.formatter.url(0))
        else:
            return (self.formatter.url(1, words[0], css=scheme, do_escape=0) +
                    self.formatter.text(words[1]) +
                    self.formatter.url(0))


    # INDENTING and LISTS ----------------------------------------------------

    def _indent_repl(self, match):
        """Handle pure indentation (no - * 1. markup)."""
        result = []
        if not (self.in_li or self.in_dd):
            self._close_item(result)
            self.in_li = 1
            css_class = None
            if self.line_was_empty and not self.first_list_item:
                css_class = 'gap'
            result.append(self.formatter.listitem(1, css_class=css_class, style="list-style-type:none"))
        return ''.join(result)

    def _li_none_repl(self, match):
        """Handle type=none (" .") lists."""
        result = []
        self._close_item(result)
        self.in_li = 1
        css_class = None
        if self.line_was_empty and not self.first_list_item:
            css_class = 'gap'
        result.append(self.formatter.listitem(1, css_class=css_class, style="list-style-type:none"))
        return ''.join(result)

    def _li_repl(self, match):
        """Handle bullet (" *") lists."""
        result = []
        self._close_item(result)
        self.in_li = 1
        css_class = None
        if self.line_was_empty and not self.first_list_item:
            css_class = 'gap'
        result.append(self.formatter.listitem(1, css_class=css_class))
        return ''.join(result)

    def _ol_repl(self, match):
        """Handle numbered lists."""
        return self._li_repl(match)

    def _dl_repl(self, match):
        """Handle definition lists."""
        result = []
        self._close_item(result)
        self.in_dd = 1
        result.extend([
            self.formatter.definition_term(1),
            self.formatter.text(match[1:-3].lstrip(' ')),
            self.formatter.definition_term(0),
            self.formatter.definition_desc(1),
        ])
        return ''.join(result)


    def _indent_level(self):
        """Return current char-wise indent level."""
        return len(self.list_indents) and self.list_indents[-1]


    def _indent_to(self, new_level, list_type, numtype, numstart):
        """Close and open lists."""
        openlist = []   # don't make one out of these two statements!
        closelist = []

        if self._indent_level() != new_level and self.in_table:
            closelist.append(self.formatter.table(0))
            self.in_table = 0

        while self._indent_level() > new_level:
            self._close_item(closelist)
            if self.list_types[-1] == 'ol':
                tag = self.formatter.number_list(0)
            elif self.list_types[-1] == 'dl':
                tag = self.formatter.definition_list(0)
            else:
                tag = self.formatter.bullet_list(0)
            closelist.append(tag)

            del self.list_indents[-1]
            del self.list_types[-1]

            if self.list_types: # we are still in a list
                if self.list_types[-1] == 'dl':
                    self.in_dd = 1
                else:
                    self.in_li = 1

        # Open new list, if necessary
        if self._indent_level() < new_level:
            self.list_indents.append(new_level)
            self.list_types.append(list_type)

            if self.formatter.in_p:
                closelist.append(self.formatter.paragraph(0))

            if list_type == 'ol':
                tag = self.formatter.number_list(1, numtype, numstart)
            elif list_type == 'dl':
                tag = self.formatter.definition_list(1)
            else:
                tag = self.formatter.bullet_list(1)
            openlist.append(tag)

            self.first_list_item = 1
            self.in_li = 0
            self.in_dd = 0

        # If list level changes, close an open table
        if self.in_table and (openlist or closelist):
            closelist[0:0] = [self.formatter.table(0)]
            self.in_table = 0

        self.in_list = self.list_types != []
        return ''.join(closelist) + ''.join(openlist)


    def _undent(self):
        """Close all open lists."""
        result = []
        #result.append("<!-- _undent start -->\n")
        self._close_item(result)
        for type in self.list_types[::-1]:
            if type == 'ol':
                result.append(self.formatter.number_list(0))
            elif type == 'dl':
                result.append(self.formatter.definition_list(0))
            else:
                result.append(self.formatter.bullet_list(0))
        #result.append("<!-- _undent end -->\n")
        self.list_indents = []
        self.list_types = []
        return ''.join(result)


    # TABLES -----------------------------------------------------------------

    def _getTableAttrs(self, attrdef):
        # skip "|" and initial "<"
        while attrdef and attrdef[0] == "|":
            attrdef = attrdef[1:]
        if not attrdef or attrdef[0] != "<":
            return {}, ''
        attrdef = attrdef[1:]

        # extension for special table markup
        def table_extension(key, parser, attrs, wiki_parser=self):
            """ returns: tuple (found_flag, msg)
                found_flag: whether we found something and were able to process it here
                  true for special stuff like 100% or - or #AABBCC
                  false for style xxx="yyy" attributes
                msg: "" or an error msg
            """
            _ = wiki_parser._
            found = False
            msg = ''
            if key[0] in "0123456789":
                token = parser.get_token()
                if token != '%':
                    wanted = '%'
                    msg = _('Expected "%(wanted)s" after "%(key)s", got "%(token)s"') % {
                        'wanted': wanted, 'key': key, 'token': token}
                else:
                    try:
                        dummy = int(key)
                    except ValueError:
                        msg = _('Expected an integer "%(key)s" before "%(token)s"') % {
                            'key': key, 'token': token}
                    else:
                        found = True
                        attrs['width'] = '"%s%%"' % key
            elif key == '-':
                arg = parser.get_token()
                try:
                    dummy = int(arg)
                except ValueError:
                    msg = _('Expected an integer "%(arg)s" after "%(key)s"') % {
                        'arg': arg, 'key': key}
                else:
                    found = True
                    attrs['colspan'] = '"%s"' % arg
            elif key == '|':
                arg = parser.get_token()
                try:
                    dummy = int(arg)
                except ValueError:
                    msg = _('Expected an integer "%(arg)s" after "%(key)s"') % {
                        'arg': arg, 'key': key}
                else:
                    found = True
                    attrs['rowspan'] = '"%s"' % arg
            elif key == '(':
                found = True
                attrs['align'] = '"left"'
            elif key == ':':
                found = True
                attrs['align'] = '"center"'
            elif key == ')':
                found = True
                attrs['align'] = '"right"'
            elif key == '^':
                found = True
                attrs['valign'] = '"top"'
            elif key == 'v':
                found = True
                attrs['valign'] = '"bottom"'
            elif key == '#':
                arg = parser.get_token()
                try:
                    if len(arg) != 6: raise ValueError
                    dummy = int(arg, 16)
                except ValueError:
                    msg = _('Expected a color value "%(arg)s" after "%(key)s"') % {
                        'arg': arg, 'key': key}
                else:
                    found = True
                    attrs['bgcolor'] = '"#%s"' % arg
            return found, self.formatter.rawHTML(msg)

        # scan attributes
        attr, msg = wikiutil.parseAttributes(self.request, attrdef, '>', table_extension)
        if msg:
            msg = '<strong class="highlight">%s</strong>' % msg
        #self.request.log("parseAttributes returned %r" % attr)
        return attr, msg

    def _tableZ_repl(self, word):
        """Handle table row end."""
        if self.in_table:
            result = ''
            # REMOVED: check for self.in_li, p should always close
            if self.formatter.in_p:
                result = self.formatter.paragraph(0)
            result += self.formatter.table_cell(0) + self.formatter.table_row(0)
            return result
        else:
            return self.formatter.text(word)

    def _table_repl(self, word):
        """Handle table cell separator."""
        if self.in_table:
            result = []
            # check for attributes
            attrs, attrerr = self._getTableAttrs(word)

            # start the table row?
            if self.table_rowstart:
                self.table_rowstart = 0
                result.append(self.formatter.table_row(1, attrs))
            else:
                # Close table cell, first closing open p
                # REMOVED check for self.in_li, paragraph should close always!
                if self.formatter.in_p:
                    result.append(self.formatter.paragraph(0))
                result.append(self.formatter.table_cell(0))

            # check for adjacent cell markers
            if word.count("|") > 2:
                if not attrs.has_key('align') and \
                   not (attrs.has_key('style') and 'text-align' in attrs['style'].lower()):
                    # add center alignment if we don't have some alignment already
                    attrs['align'] = '"center"'
                if not attrs.has_key('colspan'):
                    attrs['colspan'] = '"%d"' % (word.count("|")/2)

            # return the complete cell markup
            result.append(self.formatter.table_cell(1, attrs) + attrerr)
            return ''.join(result)
        else:
            return self.formatter.text(word)


    def _close_item(self, result):
        #result.append("<!-- close item begin -->\n")
        if self.in_table:
            self.in_table = 0
        if self.in_li:
            self.in_li = 0
        if self.in_dd:
            self.in_dd = 0

    # SCANNING ---------------------------------------------------------------
    def scan(self, scan_re, line):
        """ Scans one line
        
        Append text before match, invoke replace() with match, and add text after match.
        """
        result = []
        lastpos = 0

        ###result.append(u'<span class="info">[scan: <tt>"%s"</tt>]</span>' % line)

        for match in scan_re.finditer(line):
            # Add text before the match
            if lastpos < match.start():

                ###result.append(u'<span class="info">[add text before match: <tt>"%s"</tt>]</span>' % line[lastpos:match.start()])

                if not (self.in_pre or self.formatter.in_p):
                    result.append(self.formatter.paragraph(1, css_class="line862"))
                result.append(self.formatter.text(line[lastpos:match.start()]))

            # Replace match with markup
            if not (self.in_pre or self.formatter.in_p or
                    self.in_table or self.in_list):
                result.append(self.formatter.paragraph(1, css_class="line867"))
            result.append(self.replace(match))
            lastpos = match.end()

        ###result.append('<span class="info">[no match, add rest: <tt>"%s"<tt>]</span>' % line[lastpos:])

        # Add paragraph with the remainder of the line
        if not (self.in_pre or self.in_li or self.in_dd or
                self.formatter.in_p) and lastpos < len(line):
            result.append(self.formatter.paragraph(1, css_class="line874"))
        result.append(self.formatter.text(line[lastpos:]))
        return u''.join(result)

    def replace(self, match):
        """ Replace match using type name """
        result = []
        for type, hit in match.groupdict().items():
            if hit is not None and not type in ["hmarker", ]:

                ##result.append(u'<span class="info">[replace: %s: "%s"]</span>' % (type, hit))
                # Open p for certain types
                if not (self.formatter.in_p
                        or self.in_pre or (type in self.no_new_p_before)):
                    result.append(self.formatter.paragraph(1, css_class="line891"))

                # Get replace method and replace hit
                replace = getattr(self, '_' + type + '_repl')
                result.append(replace(hit))
                return ''.join(result)
        else:
            # We should never get here
            import pprint
            raise Exception("Can't handle match " + `match`
                + "\n" + pprint.pformat(match.groupdict())
                + "\n" + pprint.pformat(match.groups()) )

        return ""

    def format(self, formatter):
        """ For each line, scan through looking for magic
            strings, outputting verbatim any intervening text.
        """
        self.formatter = formatter
        self.hilite_re = self.formatter.page.hilite_re

        # prepare regex patterns
        rules = self.formatting_rules.replace('\n', '|')
        if self.cfg.bang_meta:
            rules = ur'(?P<notword>!%(word_rule)s)|%(rules)s' % {
                'word_rule': self.word_rule,
                'rules': rules,
            }
        pre_rules = self.pre_formatting_rules.replace('\n', '|')
        self.request.clock.start('compile_huge_and_ugly')
        scan_re = re.compile(rules, re.UNICODE)
        pre_scan_re = re.compile(pre_rules, re.UNICODE)
        number_re = re.compile(self.ol_rule, re.UNICODE)
        term_re = re.compile(self.dl_rule, re.UNICODE)
        indent_re = re.compile(ur"^\s*", re.UNICODE)
        eol_re = re.compile(r'\r?\n', re.UNICODE)
        self.request.clock.stop('compile_huge_and_ugly')

        # get text and replace TABs
        rawtext = self.raw.expandtabs()

        # go through the lines
        self.lines = eol_re.split(rawtext)
        self.line_is_empty = 0

        self.in_processing_instructions = 1

        # Main loop
        for line in self.lines:
            self.table_rowstart = 1
            self.line_was_empty = self.line_is_empty
            self.line_is_empty = 0
            self.first_list_item = 0

            # ignore processing instructions
            if self.in_processing_instructions:
                found = False
                for pi in ("##", "#format", "#refresh", "#redirect", "#deprecated",
                           "#pragma", "#form", "#acl", "#language"):
                    if line.lower().startswith(pi):
                        self.request.write(self.formatter.comment(line))
                        found = True
                        break
                if not found:
                    self.in_processing_instructions = 0
                else:
                    continue # do not parse this line
            if self.in_pre:
                # TODO: move this into function
                # still looking for processing instructions
                if self.in_pre == 'search_parser':
                    self.parser = None
                    parser_name = ''
                    if line.strip().startswith("#!"):
                        parser_name = line.strip()[2:].split()[0]
                        self.setParser(parser_name)

                    if self.parser:
                        self.in_pre = 'found_parser'
                        self.parser_lines = [line]
                        self.parser_name = parser_name
                        continue
                    else:
                        self.request.write(self.formatter.preformatted(1))
                        self.in_pre = 'no_parser'
                if self.in_pre == 'found_parser':
                    # processing mode
                    try:
                        endpos = line.index("}}}")
                    except ValueError:
                        self.parser_lines.append(line)
                        continue
                    if line[:endpos]:
                        self.parser_lines.append(line[:endpos])

                    # Close p before calling parser
                    # TODO: do we really need this?
                    res = self.formatter.parser(self.parser_name, self.parser_lines)
                    self.request.write(res)
                    del self.parser_lines
                    self.in_pre = None
                    self.parser = None

                    # send rest of line through regex machinery
                    line = line[endpos+3:]
                    if not line.strip(): # just in the case "}}} " when we only have blanks left...
                        continue
            else:
                # we don't have \n as whitespace any more
                # This is the space between lines we join to one paragraph
                line += ' '

                # Paragraph break on empty lines
                if not line.strip():
                    if self.in_table:
                        self.request.write(self.formatter.table(0))
                        self.in_table = 0
                    # CHANGE: removed check for not self.list_types
                    # p should close on every empty line
                    if self.formatter.in_p:
                        self.request.write(self.formatter.paragraph(0))
                    self.line_is_empty = 1
                    continue

                # Check indent level
                indent = indent_re.match(line)
                indlen = len(indent.group(0))
                indtype = "ul"
                numtype = None
                numstart = None
                if indlen:
                    match = number_re.match(line)
                    if match:
                        numtype, numstart = match.group(0).strip().split('.')
                        numtype = numtype[0]

                        if numstart and numstart[0] == "#":
                            numstart = int(numstart[1:])
                        else:
                            numstart = None

                        indtype = "ol"
                    else:
                        match = term_re.match(line)
                        if match:
                            indtype = "dl"

                # output proper indentation tags
                self.request.write(self._indent_to(indlen, indtype, numtype, numstart))

                # Table mode
                # TODO: move into function?                
                if (not self.in_table and line[indlen:indlen + 2] == "||"
                    and line.endswith("|| ") and len(line) >= 5 + indlen):
                    # Start table
                    if self.list_types and not self.in_li:
                        self.request.write(self.formatter.listitem(1, style="list-style-type:none"))
                        ## CHANGE: no automatic p on li
                        ##self.request.write(self.formatter.paragraph(1))
                        self.in_li = 1

                    # CHANGE: removed check for self.in_li
                    # paragraph should end before table, always!
                    if self.formatter.in_p:
                        self.request.write(self.formatter.paragraph(0))
                    attrs, attrerr = self._getTableAttrs(line[indlen+2:])
                    self.request.write(self.formatter.table(1, attrs) + attrerr)
                    self.in_table = True
                elif (self.in_table and not
                      # intra-table comments should not break a table
                      (line.startswith("##") or
                       line[indlen:indlen + 2] == "||" and
                       line.endswith("|| ") and
                       len(line) >= 5 + indlen)):

                    # Close table
                    self.request.write(self.formatter.table(0))
                    self.in_table = 0

            # Scan line, format and write
            scanning_re = self.in_pre and pre_scan_re or scan_re
            formatted_line = self.scan(scanning_re, line)
            self.request.write(formatted_line)
            if self.in_pre == 'no_parser':
                self.request.write(self.formatter.linebreak())

        # Close code displays, paragraphs, tables and open lists
        self.request.write(self._undent())
        if self.in_pre: self.request.write(self.formatter.preformatted(0))
        if self.formatter.in_p: self.request.write(self.formatter.paragraph(0))
        if self.in_table: self.request.write(self.formatter.table(0))



def convert(intext, pagemap, filemap):
    pass

if __name__ == '__main__':
    intext = """

A link using _ instead of blank: ["Other_Page"]

attachment:file%20with%20blanks.txt

"""
    pagemap = {'Other_Page': 'Other Page', }
    filemap = {'file with blanks.txt': True}
    print convert(intext, pagemap, filemap)

