import urllib
import urlparse

def url_add_params(url, escape=True, **params):
    """
    add new params to given url
    """
    pr = urlparse.urlparse(url)
    query = dict(urlparse.parse_qsl(pr.query))
    query.update(params)
    prlist = list(pr)
    if escape:
        prlist[4] = urllib.urlencode(query)
    else:
        prlist[4] = '&'.join(['%s=%s' % (k,v) for k,v in query.items()])
    return urlparse.ParseResult(*prlist).geturl()

