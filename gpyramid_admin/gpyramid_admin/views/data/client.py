#
import uuid

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPOk, HTTPNotFound

from paginate import Page

from cassandra.cqlengine.functions import Token

from pyuserdb.cassandra_.models import OAuth2Client

from gpyramid_admin.utils.paginate import PageURL_WebOb
import gpyramid_admin.forms.data.client as client_forms


ITEMS_PER_PAGE = 10


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
        if page_num < 1:
            page_num = 1

    except ValueError:
        page_num = 1

    try:
        items_per_page = int(request.params.get('per_page', ITEMS_PER_PAGE))
        if items_per_page < 1:
            items_per_page = 1

    except ValueError:
        items_per_page = ITEMS_PER_PAGE

    # Enable cassandra connection
    csdb_session = request.csdb_session

    if request.method == 'POST':
        form = client_forms.CreateClientForm(request.POST)
        if form.validate():

            # TODO: Need to create if does not exist
            OAuth2Client.create(
                name=form.name.data,
                redirect_uri=form.redirect_uri.data,
                client_type=form.client_type.data,
                home_page=form.home_page.data,
                email=form.email.data,
                client_id=form.client_id.data or str(uuid.uuid4()),
                client_secret=form.client_secret.data or str(uuid.uuid4()),
            )

            return HTTPFound(
                location=request.route_path('data.client.list_or_create')
            )

        # Else, form errors

    else:  # request.method = 'GET'
        form = client_forms.CreateClientForm()

    query = OAuth2Client.objects.all().limit(items_per_page)

    # Page to position for page being requested.
    page = list(query)
    if len(page) > 0 and page_num > 1:
        for i in xrange(page_num - 1):
            last_item = page[-1]
            page = list(query.filter(pk__token__gt=Token(last_item.pk)))

    # TODO: Paginators like to know maximum limit, not very nice in cassandra.
    page_url = PageURL_WebOb(request)
    paginator = Page(
        page, page_num,
        url_maker=page_url,
        items_per_page=items_per_page)

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

    # Enable cassandra connection
    csdb_session = request.csdb_session

    try:
        client = OAuth2Client.get(client_id=client_id)

    except OAuth2Client.DoesNotExist:
        raise HTTPNotFound

    if request.method == 'POST':
        form = client_forms.EditClientForm(request.POST)
        if form.validate():
            # Populate fields to update in user record. Skip optional fields with empty strings.
            kwargs = {
                key: value
                for key, value in form.data.items()
                if value or (form[key].flags.optional and client[key] != value)
            }
            client.update(**kwargs)

            return HTTPFound(
                location=request.route_path('data.client.view_or_edit', client_id=client.client_id)
            )

        # Else, form errors

    else:  # request.method = 'GET'
        form = client_forms.EditClientForm()

        form.client_secret.data = client.client_secret
        form.name.data = client.name
        form.client_type.data = client.client_type
        form.email.data = client.email
        form.redirect_uri.data = client.redirect_uri
        form.home_page.data = client.home_page

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

    # Enable cassandra connection
    csdb_session = request.csdb_session

    try:
        client = OAuth2Client.get(client_id=client_id)

    except OAuth2Client.DoesNotExist:
        raise HTTPNotFound

    client.delete()

    return HTTPOk()
