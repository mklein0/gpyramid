#
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPOk

from paginate import Page
from gpyramid.utils.paginate import PageURL_WebOb

import gpyramid.forms.data.user as user_forms


ITEMS_PER_PAGE = 10


import collections
import uuid
import datetime

Entry = collections.namedtuple('Entry', ['username', 'email', 'user_uuid', 'last_login_at'])



@view_config(
    route_name='data.user.list_or_create',
    renderer='data/user_list.html.mako',
    request_method=('POST', 'GET'),
)
def user_list(request):
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
        form = user_forms.CreateUserForm(request.POST)
        if form.validate():
            return HTTPFound(
                location=request.route_path('data.user.list_or_create')
            )

        # Else, form errors

    else:  # request.method = 'GET'
        form = user_forms.CreateUserForm()

    query = (
        Entry('user1', 'email@example.com', str(uuid.uuid4()), datetime.datetime.utcnow().isoformat() + 'Z'),
        Entry('user2', 'email@example.com', str(uuid.uuid4()), datetime.datetime.utcnow().isoformat() + 'Z'),
        Entry('user3', 'email@example.com', str(uuid.uuid4()), datetime.datetime.utcnow().isoformat() + 'Z'),
        Entry('user4', 'email@example.com', str(uuid.uuid4()), datetime.datetime.utcnow().isoformat() + 'Z'),
        Entry('user5', 'email@example.com', str(uuid.uuid4()), datetime.datetime.utcnow().isoformat() + 'Z'),
        Entry('user6', 'email@example.com', str(uuid.uuid4()), datetime.datetime.utcnow().isoformat() + 'Z'),
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
    route_name='data.user.view_or_edit',
    renderer='data/user_view.html.mako',
    request_method=('POST', 'GET'),
)
def user_view(request):
    """
    :param pyramid.request.Request request: Incoming Web Request
    """
    user_uuid = request.matchdict['user_uuid']

    user = Entry('user1', 'email@example.com', user_uuid, datetime.datetime.utcnow().isoformat() + 'Z')


    if request.method == 'POST':
        form = user_forms.CreateUserForm(request.POST)
        if form.validate():
            return HTTPFound(
                location=request.route_path('data.user.view_or_edit')
            )

        # Else, form errors

    else:  # request.method = 'GET'
        form = user_forms.CreateUserForm()

        form.username.data = user.username
        form.email.data = user.email

    return {
        'request': request,
        'user': user,
        'form': form,
    }


@view_config(
    route_name='data.user.view_or_edit',
    request_method='DELETE',
)
def user_delete(request):
    """
    :param pyramid.request.Request request: Incoming Web Request
    """
    user_uuid = request.matchdict['user_uuid']

    return HTTPOk()
