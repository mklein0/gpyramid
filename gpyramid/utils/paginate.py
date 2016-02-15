#
import urllib


class PageURL(object):

    def __init__(self, param_page='page', param_partial='partial'):
        self.param_page = param_page
        self.param_partial = param_partial

    def make_page_url(self, path, params, page, partial=False, sort=True):
        """A helper function for URL generators.

        Assemble a URL from its parts. Assume that a link to a certain
        page is done by overriding the 'page' query parameter.

        :param str path: the current URL path, with or without a
            "scheme://host" prefix.
        :param dict params: the current query parameters as a dict or
            dict-like object.
        :param int page: the target page number.
        :param bool partial: If true, set query param 'partial=1'. This is
            to for AJAX calls requesting a partial page.
        :param bool sort: If true (default), the query string parameters will
            be sorted. Otherwise they'll be in whatever order the dict
            iterates them.
        """
        params = params.copy()
        params[self.param_page] = page
        if partial:
            params[self.param_partial] = "1"
        if sort:
            params = params.items()
            params.sort()
        qs = urllib.urlencode(params, True)
        return '{0}?{1}'.format(path, qs)


class PageURL_WebOb(PageURL):
    """A page URL generator for WebOb-compatible Request objects.
    
    I derive new URLs based on the current URL but overriding the 'page'
    query parameter.

    I'm suitable for Pyramid, Pylons, and TurboGears, as well as any other
    framework whose Request object has 'application_url', 'path', and 'GET'
    attributes that behave the same way as ``webob.Request``'s.
    """
    
    def __init__(self, request, qualified=False, **kwargs):
        """
        ``request`` is a WebOb-compatible ``Request`` object.

        If ``qualified`` is false (default), generated URLs will have just the
        path and query string. If true, the "scheme://host" prefix will be
        included. The default is false to match traditional usage, and to avoid
        generating unuseable URLs behind reverse proxies (e.g., Apache's
        mod_proxy). 
        """
        super(PageURL_WebOb, self).__init__(**kwargs)

        self.request = request
        self.qualified = qualified

    def __call__(self, page, partial=False):
        """Generate a URL for the specified page."""
        if self.qualified:
            path = self.request.application_url
        else:
            path = self.request.path
        return self.make_page_url(path, self.request.GET, page, partial)
