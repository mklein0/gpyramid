#
from pyramid.view import view_config


@view_config(
    route_name='data.index',
    renderer='data/index.html.mako',
    request_method='GET',
)
def data_index(request):
    """
    :param pyramid.request.Request request: Incoming Web Request
    """
    return {
        'request': request,
    }