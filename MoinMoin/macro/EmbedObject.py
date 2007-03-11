# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - EmbedObject Macro

    PURPOSE:
        This macro is used to embed an object into a wiki page. Optionally, the
        size of the object can get adjusted. Further keywords are dependent on
        the kind of application.

    CALLING SEQUENCE:
        [[EmbedObject(attachment[,width=width][,height=height][,alt=Embedded mimetpye/xy])]]

    SUPPORTED MIMETYPES:  
         application/x-shockwave-flash
         application/x-dvi
         application/postscript
         application/pdf
         application/ogg
         application/vnd.visio
         
         image/x-ms-bmp
         image/svg+xml
         image/tiff
         image/x-photoshop

         audio/mpeg
         audio/midi
         audio/x-wav
                         
         video/fli
         video/mpeg
         video/quicktime
         video/x-msvideo
                         
         chemical/x-pdb

         x-world/x-vrml  
           
    INPUTS:
        attachment: name of attachment

    KEYWORD PARAMETERS:
        
        Dependent on the mimetype class a different set of keywords is used from the defaults

           width = ""
           height = ""
           alt = "Embedded mimetpye/xy"
           type = mime_type
           play = false
           loop = false
           quality = high
           op = true
           repeat = false
           autostart = false
           menu = true
      

        All do use width, height, mime_type, alt   
        
        in addition:
           'video' do use  repeat, autostart, menu, op
           'audio' do use   play, repeat, autostart, op, hidden
                   the default width is 60 and default height is 20
           'application' do use play, menu, autostart

        Note: Please do provide always a sensible alt text for the embedded object which
        gives a short description of the visually or acoustically presented content so
        that visually and acoustically impaired people can at least get a clue of what's
        going on in this "black box". By default alt is set to "Embedded mimetpye/xy" for
        people that forget to set an alt. However this default alt text is not a sensible
        one since it does not describe the content really but only the type of content.
        Compare these alt texts: "Embedded application/pdf" vs. "MoinMoin Tutorial embedded
        as PDF file"
    
    EXAMPLE:
        [[EmbedObject]]
        [[EmbedObject(example.swf,alt=A flash movie showing the rotating moin logo)]]
        [[EmbedObject(example.mid,alt=Background sound of wikipage: oceanwaves)]]
        [[EmbedObject(example.pdf)]]
        [[EmbedObject(example.svg)]]
        [[EmbedObject(example.mp3)]]
        [[EmbedObject(example.vss)]]
         
        [[EmbedObject(example.swf,width=637,height=392)]]
        [[EmbedObject(SlideShow/example.swf,width=637,height=392)]]
        [[EmbedObject(SlideShow/example.swf,width=637,height=392)]]
        [[EmbedObject(SlideShow/example.swf,width=637,height=392,play=true,loop=false)]]
        [[EmbedObject(SlideShow/example.swf,width=637,height=392,quality=low)]]

 
    PROCEDURE:
        If the attachment file isn't uploaded yet the attachment line will be shown.
        If you give only one size argument, e.g. width only, the other one will be calculated.

        By the swftools it is possible to get the swf size returned. I don't know if it is 
        possible to get sizes for svg, pdf and others detected too, that's the reason why 
        I haven't added it by now.

        Please add needed mimetypes as objects.

           
    RESTRICTIONS:
        Some mimetypes do ignore all used keywords. May be they do use different names.        


    MODIFICATION HISTORY:
        @copyright: 2006 by Reimar Bauer (R.Bauer@fz-juelich.de)      
        @license: GNU GPL, see COPYING for details.
        initial version: 1.5.0-1
        svg was added by AndrewArmstrong
        2006-05-04 TomSi: added mp3 support
        2006-05-09 RB code refactored, fixed a taintfilename bug
        2006-06-29 visio from OwenJones added but not tested,
                   RB code reviewed, taintfile removed
        2006-10-01 RB code refactored
        2006-10-05 RB bug fixed closing " at height added
        2006-10-08 RB type is needed on some platforms, some more keywords added
        2007-02-10 OliverSiemoneit: alt and noembed tags added for AccessibleMoin; fixed
                   output abstraction violation.
"""
import os, mimetypes

from MoinMoin import wikiutil
from MoinMoin.action import AttachFile

class EmbedObject:

    def __init__(self, macro, args):
        self._ = macro.request.getText
        self.macro = macro
        self.request = macro.request
        self.formatter = macro.formatter
        self.args = args

        self.width = ""
        self.height = ""
        self.alt = ""
        self.play = "false"
        self.loop = "false"
        self.quality = "high"
        self.op = "true"
        self.repeat = "false"
        self.autostart = "false"
        self.align = "center"
        self.hidden = "false"
        self.menu = "true"
        self.target = None

        if args:
            args = args.split(',')
            args = [arg.strip() for arg in args]
        else:
            args = []

        kw_count = 0
        argc = len(args)
        if args:
            for arg in self.args.split(','):
                if '=' in arg:
                    kw_count += 1
                    key, value = arg.split('=')
                    setattr(self, key, wikiutil.escape(value.strip(), quote=1))
                    argc -= kw_count
            self.target = args[0]

    def embed(self, mime_type, file):
        _ = self._
        mtype = mime_type.split('/')

        if self.alt == "":
            self.alt = "%(text)s %(mime_type)s" % {'text': _("Embedded"), 'mime_type': mime_type,}

        if mtype[0] == 'video':
            return '''
<OBJECT>
<EMBED SRC="%(file)s" WIDTH="%(width)s" HEIGHT="%(height)s" REPEAT="%(repeat)s" AUTOSTART="%(autostart)s" OP="%(op)s" MENU="%(menu)s" TYPE="%(type)s"></EMBED>
<NOEMBED>
<p>%(alt)s</p>
</NOEMBED>
</OBJECT>''' % {
    "width": self.width,
    "height": self.height,
    "file": file,
    "repeat": self.repeat,
    "autostart": self.autostart,
    "op": self.op,
    "type": mime_type,
    "menu": self.menu,
    "alt": self.alt,
}

        if mtype[0] in ['image', 'chemical', 'x-world']:
            return '''
<OBJECT>
<EMBED SRC="%(file)s" WIDTH="%(width)s" HEIGHT="%(height)s" TYPE="%(type)s"></EMBED>
<NOEMBED>
<p>%(alt)s</p>
</NOEMBED>
</OBJECT>''' % {
    "width": self.width,
    "height": self.height,
    "file": file,
    "type": mime_type,
    "alt": self.alt,
}

        if mtype[0] == 'audio':
            if self.width == "":
                self.width = "60"
            if self.height == "":
                self.height = "20"
            return '''
<OBJECT>
<EMBED SRC="%(file)s" WIDTH="%(width)s" HEIGHT="%(height)s" REPEAT="%(repeat)s" AUTOSTART="%(autostart)s" OP="%(op)s" PLAY="%(play)s" HIDDEN="%(hidden)s" TYPE="%(type)s"></EMBED>
<NOEMBED>
<p>%(alt)s</p>
</NOEMBED>
</OBJECT>''' % {
    "width": self.width,
    "height": self.height,
    "file": file,
    "play": self.play,
    "repeat": self.repeat,
    "autostart": self.autostart,
    "op": self.op,
    "hidden": self.hidden,
    "type": mime_type,
    "alt": self.alt,
}

        if mtype[0] == 'application':
            return '''
<OBJECT>
<EMBED SRC="%(file)s" WIDTH="%(width)s" HEIGHT="%(height)s" AUTOSTART="%(autostart)s" PLAY="%(play)s" LOOP="%(loop)s" MENU="%(menu)s" TYPE="%(type)s"> </EMBED>
<NOEMBED>
<p>%(alt)s</p>
</NOEMBED>
</OBJECT>''' % {
    "width": self.width,
    "height": self.height,
    "file": file,
    "autostart": self.autostart,
    "play": self.play,
    "loop": self.loop,
    "type": mime_type,
    "menu": self.menu,
    "alt": self.alt,
}

    def render(self):
        _ = self._

        if not self.target:
            msg = 'Not enough arguments to EmbedObject macro! Try [[EmbedObject(attachment [,width=width] [,height=height] [,alt=Embedded mimetpye/xy])]]'
            return "%s%s%s" % (self.formatter.sysmsg(1), self.formatter.text(msg), self.formatter.sysmsg(0))

        pagename, attname = AttachFile.absoluteName(self.target, self.formatter.page.page_name)
        attachment_fname = AttachFile.getFilename(self.request, pagename, attname)

        if not os.path.exists(attachment_fname):
            linktext = _('Upload new attachment "%(filename)s"')
            return wikiutil.link_tag(self.request,
                ('%s?action=AttachFile&rename=%s' % (
                wikiutil.quoteWikinameURL(pagename),
                wikiutil.url_quote_plus(attname))),
                linktext % {'filename': attname})

        url = AttachFile.getAttachUrl(pagename, attname, self.request)
        mime_type, enc = mimetypes.guess_type(attname)

        if mime_type in ["application/x-shockwave-flash",
                         "application/x-dvi",
                         "application/postscript",
                         "application/pdf",
                         "application/ogg",
                         "application/vnd.visio",

                         "image/x-ms-bmp",
                         "image/svg+xml",
                         "image/tiff",
                         "image/x-photoshop",

                         "audio/mpeg",
                         "audio/midi",
                         "audio/x-wav",

                         "video/fli",
                         "video/mpeg",
                         "video/quicktime",
                         "video/x-msvideo",

                         "chemical/x-pdb",

                         "x-world/x-vrml",
                       ]:
            # XXX Should better use formatter.embed if available?
            try:
                return self.macro.formatter.rawHTML(self.embed(mime_type, url))
            except:
                return "%s%s%s" % (self.macro.formatter.sysmsg(1),
                                   self.macro.formatter.text('Embedding of object by choosen formatter not possible'),
                                   self.macro.formatter.sysmsg(0))

        else:
            msg = 'Not supported mimetype %(mimetype)s ' % {"mimetype": mime_type}
            return "%s%s%s" % (self.macro.formatter.sysmsg(1),
                       self.macro.formatter.text(msg),
                       self.macro.formatter.sysmsg(0))


def execute(macro, args):
    return EmbedObject(macro, args).render()

