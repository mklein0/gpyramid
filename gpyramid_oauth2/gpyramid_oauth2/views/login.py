#
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from pyramid_oauth2_provider.interfaces import IAuthCheck
from pyramid_oauth2_provider.views import require_https

from gpyramid_oauth2.forms import login as login_forms
from gpyramid_oauth2.views.util import OAuth2AuthorizeSession


@view_config(
    route_name='login.page',
    renderer='oauth2/login.html.mako',
    request_method=('POST', 'GET'),
)
@require_https
def login_page(request):
    """
    :param pyramid.request.Request request: Incoming Web Request
    """

    if request.method == 'POST':
        form = login_forms.UserLoginForm(request.POST)

        if form.validate():
            csdb_session = request.csdb_session
            auth_check = request.registry.queryUtility(IAuthCheck)
            user_uuid = auth_check().checkauth(form.username.data, form.password.data)
            if user_uuid:
                authorize_value = OAuth2AuthorizeSession.load(request)
                authorize_value.set_user_id(str(user_uuid))

                response = HTTPFound(
                    location=request.route_path('oauth2_provider_authorize_complete', _scheme=request.scheme))

                authorize_value.set_response(response)
                authorize_value.save()

                return response

            else:
                # Invalid username/password, set error on form.
                form._error = None
                form.hidden.process_errors = form.hidden.errors = [
                    ValueError('Invalid Username/Password')
                ]
    else:
        form = login_forms.UserLoginForm()

    return {
        'request': request,
        'form': form,
    }
