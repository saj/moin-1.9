# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - modular authentication code

    @copyright: (c) Bastian Blank, Florian Festi, Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import Cookie
from MoinMoin import user

def moin_cookie(request):
    """ authenticate via the MOIN_ID cookie """
    try:
        cookie = Cookie.SimpleCookie(request.saved_cookie)
    except Cookie.CookieError:
        # ignore invalid cookies, else user can't relogin
        cookie = None
    if cookie and cookie.has_key('MOIN_ID'):
        u = user.User(request, id=cookie['MOIN_ID'].value)
        if u.valid:
            return u
    return None


"""
   idea: maybe we should call back to the request object like:
         username, password, authenticated, authtype = request.getUserPassAuth()
	 WhoEver   geheim    false          basic      (twisted, doityourself pw check)
	 WhoEver   None      true           basic/...  (apache)
	 
         thus, the server specific code would stay in request object implementation.
"""
	 
def http(request):
    """ authenticate via http basic/digest/ntlm auth """
    from MoinMoin.request import RequestTwisted
    u = None
    # check if we are running Twisted
    if isinstance(request, RequestTwisted):
        username = request.twistd.getUser()
        password = request.twistd.getPassword()
        u = user.User(request, auth_username=username, password=password)

    else:
        env = request.env
        auth_type = env.get('AUTH_TYPE','')
        if auth_type in ['Basic', 'Digest', 'NTLM', 'Negotiate',]:
            username = env.get('REMOTE_USER','')
            if auth_type in ('NTLM', 'Negotiate',):
                # converting to standard case so the user can even enter wrong case
                # (added since windows does not distinguish between e.g.
                #  "Mike" and "mike")
                username = username.split('\\')[-1] # split off domain e.g.
                                                    # from DOMAIN\user
                # this "normalizes" the login name from {meier, Meier, MEIER} to Meier
                # put a comment sign in front of next line if you don't want that:
                username = username.title()
            u = user.User(request, auth_username=username)

    if u:
        u.create_or_update()
    if u and u.valid:
        return u
    else:
        return None

def sslclientcert(request):
    """ authenticate via SSL client certificate """
    from MoinMoin.request import RequestTwisted
    u = None
    # check if we are running Twisted
    if isinstance(request, RequestTwisted):
        return u # not supported if we run twisted
        # Addendum: this seems to need quite some twisted insight and coding.
        # A pointer i got on #twisted: divmod's vertex.sslverify
        # If you really need this, feel free to implement and test it and
        # submit a patch if it works.
    else:
        env = request.env
        if env.get('SSL_CLIENT_VERIFY', 'FAILURE') == 'SUCCESS':
            # if we only want to accept some specific CA, do a check like:
            # if env.get('SSL_CLIENT_I_DN_OU') == "http://www.cacert.org"
            email = env.get('SSL_CLIENT_S_DN_Email', '')
            email_lower = email.lower()
            commonname = env.get('SSL_CLIENT_S_DN_CN', '')
            commonname_lower = commonname.lower()
            if email_lower or commonname_lower:
                for uid in user.getUserList():
                    u = user.User(request, uid)
                    if email_lower and u.email.lower() == email_lower:
                        break
                    if commonname_lower and u.name.lower() == commonname_lower:
                        break
                else:
                    u = None
                #u = user.User(request, auth_username=username)

    if u:
        u.create_or_update()
    if u and u.valid:
        return u
    else:
        return None

def interwiki(request):
    if request.form.has_key("user"):
        username = request.form["user"][0]
    else:
        return None
    passwd = None
    if request.form.has_key("passwd"):
        passwd = request.form["passwd"][0]

    wikitag, wikiurl, wikitail, err = wikiutil.resolve_wiki(username)

    if err or wikitag not in request.cfg.trusted_wikis:
        return None
    
    if passwd:
        import xmlrpclib
        homewiki = xmlrpclib.Server(wikiurl + "?action=xmlrpc2")
        account_data = homewiki.getUser(wikitail, passwd)
        if isinstance(account_data, str):
            # show error message
            return None
        
        u = user.User(request, name=username)
        for key, value in account_data.iteritems():
            if key not in ["may", "id", "valid", "trusted"
                           "auth_username",
                           "name", "aliasname",
                           "enc_passwd"]:
                setattr(u, key, value)
        u.save()
        request.user = u
        request.setCookie()
        return u
    else:
        pass
        # XXX redirect to homewiki

