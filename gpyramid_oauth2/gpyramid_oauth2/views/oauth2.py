#
"""
Rewrite the views in pyramid_oauth2_provider to use cassandra models.
"""
import datetime
import logging
from urllib import urlencode
from urlparse import urlparse, parse_qsl, ParseResult

from pyramid.httpexceptions import HTTPFound
from pyramid.security import (
    NO_PERMISSION_REQUIRED,
)
from pyramid.view import view_config
from pyramid_oauth2_provider.errors import (
    InvalidToken,
    InvalidClient,
    InvalidRequest,
    UnsupportedGrantType,
    BaseOauth2Error,
    # InvalidGrant,
)
from pyramid_oauth2_provider.generators import gen_token
from pyramid_oauth2_provider.interfaces import IAuthCheck
from pyramid_oauth2_provider.jsonerrors import HTTPBadRequest, HTTPUnauthorized, HTTPMethodNotAllowed
from pyramid_oauth2_provider.util import getClientCredentials
from pyramid_oauth2_provider.views import require_https, add_cache_headers

from gpyramid_oauth2.views.util import OAuth2AuthorizeSession
from pyuserdb.cassandra_.models import (
    User,
    OAuth2Client,
    OAuth2GrantAuthorization,
    OAuth2TokenAccess,
    OAuth2TokenRefresh,
)


class InvalidGrant(BaseOauth2Error):
    """
    The provided authorization grant (e.g., authorization
    code, resource owner credentials) or refresh token is
    invalid, expired, revoked, does not match the redirection
    URI used in the authorization request, or was issued to
    another client.

    https://tools.ietf.org/html/rfc6749#section-5.2
    """
    error_name = 'invalid_grant'


log = logging.getLogger('gpyramid_oauth2.views')


def handle_base_authorize_request(request):
    """
    Provide basic validatation of incoming authorize request.

    :param pyramid.request.Request request: Incoming Web Request

    :return: Validated OAuth2 Client record, redirection URI override if present and valid
    :rtype: pyuserdb.cassandra_.OAuth2Client, str
    """
    request.client_id = request.params.get('client_id')

    csdb_session = request.csdb_session
    try:
        if not request.client_id:
            raise OAuth2Client.DoesNotExist
        client = OAuth2Client.get(client_id=request.client_id)

    except OAuth2Client.DoesNotExist:
        log.info('received invalid client credentials')
        raise HTTPBadRequest(InvalidRequest(
            error_description='Invalid client credentials'))

    import ipdb; ipdb.set_trace()
    redirect_found = False
    redirection_uri = None
    redirect_uri = request.params.get('redirect_uri')
    if client.redirect_uri:
        if not redirect_uri:
            # No redirect passed, use default one.
            redirect_found = True

        elif redirect_uri.startswith(client.redirect_uri):
            # Redirect passed, make sure it matches start of the one we have.
            redirection_uri = redirect_uri
            redirect_found = True

    # if len(client.redirect_uris) == 1:
    #     # Only one redirect URI configured for client, given redirect uri is configured URI or starts with
    #     # uri specification
    #     if not redirect_uri:
    #         redirection_uri = client.redirect_uris[0]
    #
    #     elif redirect_uri.startswith(client.redirect_uris[0]):
    #         redirection_uri = redirect_uri
    #
    #     # Else, Invalid redirect uri passed
    #
    # elif len(client.redirect_uris) > 0:
    #     # Multiple redirect uris configured, must match one of them exactly.
    #     for i in client.redirect_uris:
    #         if redirect_uri == i:
    #             redirection_uri = redirect_uri
    #             break

    # Else, No redirect uris configured for client. The redirect will never find a partial match.

    if not redirect_found:
        return HTTPBadRequest(InvalidRequest(
            error_description='Redirection URI validation failed'))

    return client, redirection_uri


@view_config(
    route_name='oauth2_provider_authorize',
    renderer='json',
    request_param='response_type=code',
    permission=NO_PERMISSION_REQUIRED,
)
@require_https
def oauth2_authorize_code(request):
    """
    :param pyramid.request.Request request: Incoming Web Request

    * In the case of a 'code' authorize request a GET or POST is made
    with the following structure.

        GET /authorize?response_type=code&client_id=aoiuer HTTP/1.1
        Host: server.example.com

        POST /authorize HTTP/1.1
        Host: server.example.com
        Content-Type: application/x-www-form-urlencoded

        response_type=code&client_id=aoiuer

    The response_type and client_id are required parameters. A redirect_uri
    and state parameters may also be supplied. The redirect_uri will be
    validated against the URI's registered for the client. The state is an
    opaque value that is simply passed through for security on the client's
    end.

    The response to a 'code' request will be a redirect to a registered URI
    with the authorization code and optional state values as query
    parameters.

        HTTP/1.1 302 Found
        Location: https://client.example.com/cb?code=AverTaer&state=efg

    """
    client, redirection_uri = handle_base_authorize_request(request)

    state = request.params.get('state')
    resp = handle_authorize_authcode(request, client, redirection_uri, state)
    return resp


@view_config(
    route_name='oauth2_provider_authorize',
    renderer='json',
    request_param='response_type=token',
    permission=NO_PERMISSION_REQUIRED,
)
@require_https
def oauth2_authorize_implicit(request):
    """

    :param pyramid.request.Request request: Incoming Web Request
    """
    client, redirection_uri = handle_base_authorize_request(request)

    state = request.params.get('state')
    resp = handle_authorize_implicit(request, client, redirection_uri, state)
    return resp


@view_config(
    route_name='oauth2_provider_authorize',
    renderer='json',
    permission=NO_PERMISSION_REQUIRED,
)
@require_https
def oauth2_authorize(request):
    """
    * In the case of a 'code' authorize request a GET or POST is made
    with the following structure.

        GET /authorize?response_type=code&client_id=aoiuer HTTP/1.1
        Host: server.example.com

        POST /authorize HTTP/1.1
        Host: server.example.com
        Content-Type: application/x-www-form-urlencoded

        response_type=code&client_id=aoiuer

    The response_type and client_id are required parameters. A redirect_uri
    and state parameters may also be supplied. The redirect_uri will be
    validated against the URI's registered for the client. The state is an
    opaque value that is simply passed through for security on the client's
    end.

    The response to a 'code' request will be a redirect to a registered URI
    with the authorization code and optional state values as query
    parameters.

        HTTP/1.1 302 Found
        Location: https://client.example.com/cb?code=AverTaer&state=efg

    """
    log.info('received invalid response_type %s', request.params.get('response_type', '<Missing>'))
    resp = HTTPBadRequest(InvalidRequest(
        error_description='Oauth2 unknown response_type not supported'))

    return resp


def handle_authorize_authcode(request, client, redirection_uri, state=None):
    """
    Setup an authorization code session.

    :param pyramid.request.Request request: Incoming Web Request
    :param pyuserdb.cassandra_.models.OAuth2Client client: OAuth2 Client Record
    :param str redirection_uri: redirection URI associated with client
    :param str | None state: optional state string

    :return:
    """

    # Optional fields
    # resource scope if present.
    scope = request.params.get('scope')
    if scope:
        scope = scope.strip().split(' ')

    # Setup temporary state for login
    # TODO: This could be a sparser dict
    # TODO: Consider using pyramid session manager and other modules.
    # For now lets manage things via cookies.
    response = HTTPFound(
        location=request.route_path('login.page', _scheme=request.scheme)
    )
    authorize_value = OAuth2AuthorizeSession(request, response)
    authorize_value.update(
        client_id=str(client.client_id),
        redirect_uri=redirection_uri,
        scope=scope,
        state=state,
    )
    authorize_value.save()

    return response


@view_config(
    route_name='oauth2_provider_authorize_complete',
    permission=NO_PERMISSION_REQUIRED,
)
@require_https
def oauth2_authorize_complete(request):
    """

    :param pyramid.request.Request request: Incoming Web Request
    """
    try:
        authorize_value = OAuth2AuthorizeSession.load(request)

    except ValueError:
        log.info('authorize complete without cookie')
        raise HTTPBadRequest(InvalidRequest(
            error_description='Invalid client credentials'))

    # Load Client
    csdb_session = request.csdb_session
    try:
        client = OAuth2Client.get(client_id=authorize_value['client_id'])

    except OAuth2Client.DoesNotExist:
        log.info('received invalid client credentials')
        raise HTTPBadRequest(InvalidRequest(
            error_description='Invalid client credentials'))

    # user_id = authenticated_userid(request)
    try:
        user = User.get(user_uuid=authorize_value['user_uuid'])
        user_id = user.user_uuid

    except User.DoesNotExist:
        user_id = None

    if not user_id:
        log.info('User ID did not exist')
        raise HTTPBadRequest(InvalidRequest(
            error_description='Invalid client credentials'))

    return handle_authorize_complete_authcode(
        request, client, user_id,
        authorize_value['redirect_uri'], authorize_value['state'], authorize_value['scope'])


def handle_authorize_complete_authcode(request, client, user_id, redirection_uri, state=None, scope=None):
    """
    Setup an authorization code session.

    :param pyramid.request.Request request: Incoming Web Request
    :param pyuserdb.cassandra_.models.OAuth2Client client: OAuth2 Client Record
    :param uuid.UUID user_id: UUID for user
    :param str redirection_uri: redirection URI associated with client
    :param str | None state: optional state string
    :param list[str] | None scope: optional scope strings

    :return:
    """
    parts = urlparse(redirection_uri or client.redirect_uri)
    qparams = dict(parse_qsl(parts.query))

    # Create AuthCode
    auth_code = OAuth2GrantAuthorization.create(
        client_id=client.client_id,
        user_uuid=user_id,
        authorization_code=gen_token(client),
        redirect_uri=redirection_uri,
        valid_until=(datetime.datetime.utcnow() + datetime.timedelta(seconds=60*60)),
        scope=scope,
        state=state,
    )

    qparams['code'] = auth_code.authorization_code
    if state:
        qparams['state'] = state
    parts = ParseResult(
        parts.scheme, parts.netloc, parts.path, parts.params,
        urlencode(qparams), '')
    return HTTPFound(location=parts.geturl())


def handle_authorize_implicit(request, client, redirection_uri, state=None):
    """

    :param pyramid.request.Request request: Incoming Web Request
    :param pyuserdb.cassandra_.models.OAuth2Client client: OAuth2 Client Record
    :param str redirection_uri: redirection URI associated with client
    :param str | None state: optional state string

    :return:
    """
    return HTTPBadRequest(InvalidRequest(
        error_description='Oauth2 response_type "implicit" not supported'))


@view_config(
    route_name='oauth2_provider_token',
    renderer='json',
    request_method='POST',
    request_param='grant_type=authorization_code',
    permission=NO_PERMISSION_REQUIRED
)
@require_https
def oauth2_token_authorization_code(request):
    """
    :param pyramid.request.Request request: Incoming Web Request

    * In the case of an incoming authentication request a POST is made
    with the following structure.

        POST /token HTTP/1.1
        Host: server.example.com
        Authorization: Basic czZCaGRSa3F0MzpnWDFmQmF0M2JW
        Content-Type: application/x-www-form-urlencoded

        grant_type=authorization_code&code=SplxlOBeZQQYbYS6WxSbIA

    The client_id and code are form encoded as part of the body. This
    request *must* be made over https.

    The response to this request will be, assuming no error:

        HTTP/1.1 200 OK
        Content-Type: application/json;charset=UTF-8
        Cache-Control: no-store
        Pragma: no-cache

        {
          "access_token":"2YotnFZFEjr1zCsicMWpAA",
          "token_type":"bearer",
          "expires_in":3600,
          "refresh_token":"tGzv3JOkF0XG5Qx2TlKW",
          "user_id": 1234,
        }
    """
    # getClientCredentials(request)
    #
    # # Make sure we got a client_id and secret through the authorization
    # # policy. Note that you should only get here if not using the Oauth2
    # # authorization policy or access was granted through the AuthTKt policy.
    # if hasattr(request, 'client_id') and request.client_id == request.POST.get('client_id'):
    #     log.info('did not matching client credentials')
    #     return HTTPUnauthorized('Invalid client credentials')
    request.client_id = request.POST.get('client_id')

    csdb_session = request.csdb_session
    try:
        if request.client_id is None:
            raise OAuth2Client.DoesNotExist
        client = OAuth2Client.get(client_id=request.client_id)

    except OAuth2Client.DoesNotExist:
        log.info('received invalid client credentials')
        return HTTPBadRequest(InvalidRequest(
            error_description='Invalid client credentials'))

    # Check for supported grant type. This is a required field of the form
    # submission.
    resp = handle_token_authorization_code(request, client)

    add_cache_headers(request)
    return resp


@view_config(
    route_name='oauth2_provider_token',
    renderer='json',
    request_method='POST',
    request_param='grant_type=password',
    permission=NO_PERMISSION_REQUIRED
)
@require_https
def oauth2_token_password(request):
    """
    :param pyramid.request.Request request: Incoming Web Request

    * In the case of an incoming authentication request a POST is made
    with the following structure.

        POST /token HTTP/1.1
        Host: server.example.com
        Authorization: Basic czZCaGRSa3F0MzpnWDFmQmF0M2JW
        Content-Type: application/x-www-form-urlencoded

        grant_type=password&username=johndoe&password=A3ddj3w

    The basic auth header contains the client_id:client_secret base64
    encoded for client authentication.

    The username and password are form encoded as part of the body. This
    request *must* be made over https.

    The response to this request will be, assuming no error:

        HTTP/1.1 200 OK
        Content-Type: application/json;charset=UTF-8
        Cache-Control: no-store
        Pragma: no-cache

        {
          "access_token":"2YotnFZFEjr1zCsicMWpAA",
          "token_type":"bearer",
          "expires_in":3600,
          "refresh_token":"tGzv3JOkF0XG5Qx2TlKW",
          "user_id":1234,
        }
    """

    # Make sure this is a POST.
    if request.method != 'POST':
        log.info('rejected request due to invalid method: %s' % request.method)
        return HTTPMethodNotAllowed(
            'This endpoint only supports the POST method.')

    getClientCredentials(request)

    # Make sure we got a client_id and secret through the authorization
    # policy. Note that you should only get here if not using the Oauth2
    # authorization policy or access was granted through the AuthTKt policy.
    if (not hasattr(request, 'client_id') or
            not hasattr(request, 'client_secret')):
        log.info('did not receive client credentials')
        return HTTPUnauthorized('Invalid client credentials')

    csdb_session = request.csdb_session
    try:
        client = OAuth2Client.get(client_id=request.client_id)

    except OAuth2Client.DoesNotExist:
        client = None

    # Again, the authorization policy should catch this, but check again.
    if not client or client.client_secret != request.client_secret:
        log.info('received invalid client credentials')
        return HTTPBadRequest(InvalidRequest(
            error_description='Invalid client credentials'))

    # Check for supported grant type. This is a required field of the form
    # submission.
    resp = handle_token_password(request, client)

    add_cache_headers(request)
    return resp


@view_config(
    route_name='oauth2_provider_token',
    renderer='json',
    request_method='POST',
    request_param='grant_type=refresh_token',
    permission=NO_PERMISSION_REQUIRED
)
@require_https
def oauth2_token_refresh(request):
    """
    :param pyramid.request.Request request: Incoming Web Request

    * In the case of an incoming refresh token request a POST is made
    with the following structure.

        POST /token HTTP/1.1
        Host: server.example.com
        Authorization: Basic czZCaGRSa3F0MzpnWDFmQmF0M2JW
        Content-Type: application/x-www-form-urlencoded

        grant_type=refresh_token&refresh_token=tGzv3JOkF0XG5Qx2TlKW&user_id=1234

    The response to this request will be, assuming no error:

        HTTP/1.1 200 OK
        Content-Type: application/json;charset=UTF-8
        Cache-Control: no-store
        Pragma: no-cache

        {
          "access_token":"2YotnFZFEjr1zCsicMWpAA",
          "token_type":"bearer",
          "expires_in":3600,
          "refresh_token":"tGzv3JOkF0XG5Qx2TlKW",
          "user_id":1234,
        }

    """
    getClientCredentials(request)

    # Make sure we got a client_id and secret through the authorization
    # policy. Note that you should only get here if not using the Oauth2
    # authorization policy or access was granted through the AuthTKt policy.
    if (not hasattr(request, 'client_id') or
            not hasattr(request, 'client_secret')):
        log.info('did not receive client credentials')
        return HTTPUnauthorized('Invalid client credentials')

    csdb_session = request.csdb_session
    try:
        client = OAuth2Client.get(client_id=request.client_id)

    except OAuth2Client.DoesNotExist:
        client = None

    # Again, the authorization policy should catch this, but check again.
    if not client or client.client_secret != request.client_secret:
        log.info('received invalid client credentials')
        return HTTPBadRequest(InvalidRequest(
            error_description='Invalid client credentials'))

    # Check for supported grant type. This is a required field of the form
    # submission.
    resp = handle_token_refresh(request, client)

    add_cache_headers(request)
    return resp


@view_config(
    route_name='oauth2_provider_token',
    renderer='json',
    permission=NO_PERMISSION_REQUIRED
)
@require_https
def oauth2_token(request):
    """
    :param pyramid.request.Request request: Incoming Web Request

    The incoming request does not match one of a password grant, token refresh, or authorization code grant.

    This is a bad request.
    """

    # Make sure this is a POST.
    if request.method != 'POST':
        log.info('rejected request due to invalid method: %s' % request.method)
        return HTTPMethodNotAllowed(
            'This endpoint only supports the POST method.')

    # Find out what unsupported grant type is being requested. This is a required field of the form
    # submission.
    grant_type = request.POST.get('grant_type', '<Missing>')

    log.info('invalid grant type: %s' % grant_type)
    resp = HTTPBadRequest(UnsupportedGrantType(
        error_description='Only password and refresh_token grant types are supported by this authentication server'))

    return resp


def token_as_json(refresh_token, expires_in, **kwargs):
    """

    :param pyuserdb.cassandra_.models.OAuth2TokenRefresh refresh_token: Pending RefreshToken
    :param int expires_in: Number of seconds until token expires
    :param dict kwargs: Addtional keyword arguments to add to resulting dict.

    :return:
    """
    token = {
        'access_token': refresh_token.access_token,
        'refresh_token': refresh_token.refresh_token,
        'user_id': str(refresh_token.user_uuid),
        'expires_in': expires_in,
    }
    kwargs.update(token)
    return kwargs


def create_token_set(client, user_uuid):
    """

    :param pyuserdb.cassandra_.models.OAuth2Client client: OAuth2 Client
    :param uuid.UUID user_uuid: User UUID
    :return:
    """
    access_token = OAuth2TokenAccess.create(
        access_token=gen_token(client),
        user_uuid=user_uuid,
        client_id=client.client_id,
    )
    refresh_token = OAuth2TokenRefresh.create(
        refresh_token=gen_token(client),
        access_token=access_token.access_token,
        user_uuid=access_token.user_uuid,
        client_id=access_token.client_id,
    )

    return access_token, refresh_token


def handle_token_authorization_code(request, client):
    """
    https://tools.ietf.org/html/rfc6749#section-4.1.3

    :param pyramid.request.Request request: Incoming Web Request
    :param pyuserdb.cassandra_.models.OAuth2Client client: OAuth2 Client

    :return:
    """
    redirect_uri = request.POST.get('redirect_uri')
    code = request.POST.get('code')

    redirection_uri = client.redirect_uri
    try:
        if code is None:
            raise OAuth2GrantAuthorization.DoesNotExist
        auth_grant = OAuth2GrantAuthorization.get(authorization_code=code)

    except OAuth2GrantAuthorization.DoesNotExist:
        log.info('Invalid authorization code')
        return HTTPBadRequest(InvalidGrant(
            error_description=''))

    if auth_grant.redirect_uri:
        if auth_grant.redirect_uri != redirect_uri:
            log.info('Redirection URI mismatch')
            return HTTPBadRequest()

        # Else, redirect uri matches
        redirection_uri = redirect_uri

    elif redirect_uri:
        if redirect_uri != client.redirect_uri:
            log.info('Given redirect does not match client')
            return HTTPBadRequest()

        # Else, redirect uri matches. use clients version

    # Else, redirect is implicitly one in client.

    # TODO: Check valid until, or force TTL on record?

    access_token, refresh_token = create_token_set(client, auth_grant.user_uuid)
    auth_grant.delete()

    expires_in = access_token.valid_until
    return token_as_json(refresh_token, expires_in, token_type='bearer')


def handle_token_password(request, client):
    """

    :param pyramid.request.Request request: Incoming Web Request
    :param pyuserdb.cassandra_.models.OAuth2Client client: OAuth2 Client

    :return:
    """
    # Do not hold password in local memory
    if 'username' not in request.POST or 'password' not in request.POST:
        log.info('missing username or password')
        return HTTPBadRequest(InvalidRequest(
            error_description='Both username and password are required to obtain a password based grant.'))

    auth_check = request.registry.queryUtility(IAuthCheck)
    user_id = auth_check().checkauth(request.POST.get('username'),
                                     request.POST.get('password'))

    if not user_id:
        log.info('could not validate user credentials')
        return HTTPUnauthorized(InvalidClient(error_description='Username and '
            'password are invalid.'))

    access_token, refresh_token = create_token_set(client, user_id)

    expires_in = access_token.valid_until
    return token_as_json(refresh_token, expires_in, token_type='bearer')


def handle_token_refresh(request, client):
    """

    :param pyramid.request.Request request: Incoming Web Request
    :param pyuserdb.cassandra_.models.OAuth2Client client: OAuth2 Client

    :return:
    """
    if 'refresh_token' not in request.POST:
        log.info('refresh_token field missing')
        return HTTPBadRequest(InvalidRequest(error_description='refresh_token '
            'field required'))

    if 'user_id' not in request.POST:
        log.info('user_id field missing')
        return HTTPBadRequest(InvalidRequest(error_description='user_id '
            'field required'))

    try:
        refresh_token = OAuth2TokenRefresh.get(refresh_token=request.POST.get('refresh_token'))

    except OAuth2Client.DoesNotExist:
        log.info('invalid refresh_token')
        return HTTPUnauthorized(InvalidToken(error_description='Provided '
            'refresh_token is not valid.'))

    if refresh_token.client_id != client.client_id:
        log.info('invalid client_id')
        return HTTPBadRequest(InvalidClient(error_description='Client does '
            'not own this refresh_token.'))

    if refresh_token.user_uuid != request.POST.get('user_id'):
        log.info('invalid user_id')
        return HTTPBadRequest(InvalidClient(error_description='The given '
            'user_id does not match the given refresh_token.'))

    # Refresh Token valid, revoke old token, create new one.
    try:
        OAuth2TokenAccess.get(access_token=refresh_token.access_token).delete()

    except OAuth2TokenAccess.DoesNotExist:
        pass

    new_access_token, new_refresh_token = create_token_set(client, refresh_token.user_uuid)
    refresh_token.delete()

    expires_in = new_access_token.valid_until
    return token_as_json(new_refresh_token, expires_in, token_type='bearer')
