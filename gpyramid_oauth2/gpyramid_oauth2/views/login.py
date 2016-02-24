#
from pyramid.view import view_config

from pyramid_oauth2_provider.interfaces import IAuthCheck


@view_config(
    route_name='login.page',
    renderer='oauth2/login.html.mako',
    request_method=('POST', 'GET'),
)
def login_page(request):
    """
    :param pyramid.request.Request request: Incoming Web Request
    """

    auth_check = request.registry.queryUtility(IAuthCheck)
    user_id = auth_check().checkauth(request.POST.get('username'),
                                     request.POST.get('password'))