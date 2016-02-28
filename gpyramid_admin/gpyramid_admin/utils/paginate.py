#
import urllib

from cassandra.cqlengine.functions import Token


class PageURL(object):

    def __init__(self, param_page='page', param_partial='partial'):
        """
        :param str param_page: Name of Query String parameter to contain the current page number.
        :param str param_partial: Name of Query String parameter to contain the partial flag.
        """
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

        :return: Return URL with given Query String and additional pagination parameters
        :rtype: str
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
        """
        Generate a URL for the specified page.

        :param int page: Current Page number to generate URL for
        :param bool partial: A flag.

        :return: Return URL with given Query String and additional pagination parameters
        :rtype: str

        """
        if self.qualified:
            path = self.request.application_url
        else:
            path = self.request.path
        return self.make_page_url(path, self.request.GET, page, partial)


class PageCollection_CassandraCQLEngine(object):

    def __init__(self, items_per_page, query, len_=None):
        """

        :param int items_per_page: Number of items per page
        :param query: Cassandra CQLEngine Query
        """
        if items_per_page < 1:
            items_per_page = 1

        self.query = query.limit(items_per_page)
        self.items_per_page = items_per_page
        self._len = len_
        self.page_num = 0
        self.page = None
        self.finished = False

    def copy(self):
        """
        Make a new copy of the current object with reset state.

        :rtype: PageCollection_CassandraCQLEngine
        """
        return type(self)(self.query, self.items_per_page, len_=self._len)

    def full_copy(self):
        """
        Make a new copy of the current object with reset state.

        :rtype: PageCollection_CassandraCQLEngine
        """
        obj = type(self)(self.query, self.items_per_page, len_=self._len)
        obj.page_num = self.page_num
        obj.finished = self.finished
        obj.page = self.page

        return obj

    def next_page(self):
        # Page to position for page being requested.
        if self.page is None:
            page_num = self.page_num = 1
            page = self.page = list(self.query)

        else:
            # First page already exists, get next
            if self.finished or len(self.page) < self.items_per_page:
                # Less data then expected, must be over
                self._len = (self.page_num - 1) * self.items_per_page + len(self.page)
                self.finished = True
                return None

            # Else, get next page of elements
            last_item = self.page[-1]
            page = list(self.query.filter(pk__token__gt=Token(last_item.pk)))
            page_num = self.page_num + 1
            if len(page) > 0:
                self.page_num = page_num
                self.page = page

        if len(page) < self.items_per_page:
            # Less data then expected, must be over
            self._len = (page_num - 1) * self.items_per_page + len(page)
            self.finished = True

        # Return next page
        return page

    def page_has_index(self, index):
        # Can we meet need?
        if self.page_num == 0:
            return False

        window_start = (self.page_num - 1) * self.items_per_page
        window_end = self.page_num * self.items_per_page

        return window_start <= index and index < window_end

    def page_before_index(self, index):
        if self.page_num == 0:
            return True

        window_end = self.page_num * self.items_per_page

        return window_end <= index

    def _getitem_to_page(self, index):
        need_page, loc = divmod(index, self.items_per_page)
        need_page += 1
        while not self.finished and self.page_num < need_page:
            self.next_page()

        if self.page_num != need_page:
            raise IndexError('index out of range')

        return loc

    def _getitem_single(self, index):
        """
        :param int index: Location of item seeking

        :return:
        :rtype: object
        """
        if index < 0:
            raise IndexError('Negative indices are not supported.')

        if self.page_has_index(index):
            if self.page is None:
                # Need to prime the pump.
                self.next_page()

            loc = index - (self.page_num - 1) * self.items_per_page
            return self.page[loc]

        elif self.page_before_index(index):
            # We can iterate forward to position
            loc = self._getitem_to_page(index)

            return self.page[loc]

        # Else, The item request has already been passed. Create a new pager and start over.
        worker = self.copy()
        return worker[index]


    def _getitem_iter(self, start, stop, step):
        """
        :param int start: starting index
        :param int stop: stoping index
        :param int step: steps to take towards stop

        :return:
        :rtype: collections.Iterable[object]
        """
        pos = start
        while stop is None or pos < stop:
            try:
                loc = self._getitem_to_page(pos)

                yield self.page[loc]

                pos += step

            except IndexError:
                # End of iterations, stop
                return


    def _getitem_slice(self, index):
        """
        :param slice index: Location of items seeking

        :return:
        :rtype: collections.Iterable[object]
        """
        if isinstance(index.start, int):
            if index.start < 0:
                raise IndexError('Negative indices are not supported.')

        elif index.start is not None:
            raise IndexError('Invalid index type: {}'.format(type(index.start)))

        if isinstance(index.stop, int):
            if index.stop < 0:
                raise IndexError('Negative indices are not supported.')

        elif index.stop is not None:
            raise IndexError('Invalid index type: {}'.format(type(index.stop)))

        if isinstance(index.step, int):
            if index.step < 0:
                raise IndexError('Negative indices are not supported.')

        elif index.step is not None:
            raise IndexError('Invalid index type: {}'.format(type(index.step)))

        start = index.start or 0
        step = index.step or 1

        if self.page_has_index(start) or self.page_before_index(start):
            # Iterate on current object
            return  self._getitem_iter(start, index.stop, step)

        # Else, Need to create a worker to iterate via
        worker = self.copy()
        return worker[index]

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self._getitem_slice(index)

        elif isinstance(index, int):
            return self._getitem_single(index)

        else:
            raise IndexError('Invalid index type: {}'.format(type(index)))

    def __len__(self):
        if self._len is not None:
            return self._len

        # Else, rough guess is current page + 1
        return max(1, self.page_num) * self.items_per_page + 1