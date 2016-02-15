#
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPOk

from paginate import Page
from gpyramid.utils.paginate import PageURL_WebOb

import gpyramid.forms.data.client as client_forms


ITEMS_PER_PAGE = 10


import collections
import uuid
import datetime

Entry = collections.namedtuple('Entry', [
    'client_id', 'client_secret', 'email', 'redirect_uri'
    ])



@view_config(
    route_name='data.client.list_or_create',
    renderer='data/client_list.html.mako',
    request_method=('POST', 'GET'),
)
def client_list(request):
    """
    :param pyramid.request.Request request: Incoming Web Request
    """
    try:
        page_num = int(request.params.get('page', 1))
    except ValueError:
        page_num = 1
    try:
        items_per_page = int(request.params.get('per_page', ITEMS_PER_PAGE))
    except ValueError:
        items_per_page = ITEMS_PER_PAGE


    if request.method == 'POST':
        form = client_forms.CreateClientForm(request.POST)
        if form.validate():
            return HTTPFound(
                location=request.route_path('data.client.list_or_create')
            )

        # Else, form errors

    else:  # request.method = 'GET'
        form = client_forms.CreateClientForm()

    query = (
        Entry(str(uuid.uuid4()), str(uuid.uuid4()), 'email@example.com', 'http://localhost.local/redirect'),
        Entry(str(uuid.uuid4()), str(uuid.uuid4()), 'email@example.com', 'http://localhost.local/redirect'),
        Entry(str(uuid.uuid4()), str(uuid.uuid4()), 'email@example.com', 'http://localhost.local/redirect'),
        Entry(str(uuid.uuid4()), str(uuid.uuid4()), 'email@example.com', 'http://localhost.local/redirect'),
    )

    page_url = PageURL_WebOb(request)
    paginator = Page(
        query, page_num,
        url_maker=page_url,
        items_per_page=items_per_page,
        item_count=len(query))

    return {
        'request': request,
        'page_num': page_num,
        'items_per_page': items_per_page,
        'paginator': paginator,
        'form': form,
    }


@view_config(
    route_name='data.client.view_or_edit',
    renderer='data/client_view.html.mako',
    request_method=('POST', 'GET'),
)
def client_view(request):
    """
    :param pyramid.request.Request request: Incoming Web Request
    """
    client_id = request.matchdict['client_id']

    client = Entry(
        client_id, str(uuid.uuid4()),
        'email@example.com', 'http://localhost.local/redirect')

    if request.method == 'POST':
        form = client_forms.CreateClientForm(request.POST)
        if form.validate():
            return HTTPFound(
                location=request.route_path('data.client.view_or_edit', client_id=client.client_id)
            )

        # Else, form errors

    else:  # request.method = 'GET'
        form = client_forms.CreateClientForm()

        form.client_secret.data = client.client_secret
        form.email.data = client.email
        form.redirect_uri.data = client.redirect_uri

    return {
        'request': request,
        'client': client,
        'form': form,
    }


@view_config(
    route_name='data.client.view_or_edit',
    request_method='DELETE',
)
def client_delete(request):
    """
    :param pyramid.request.Request request: Incoming Web Request
    """
    client_id = request.matchdict['client_id']

    return HTTPOk()
