#
"""
Rewrite the views in pyramid_oauth2_provider to use cassandra models.
"""
import datetime
import logging

from pyramid.view import view_config
from pyramid.security import (
    NO_PERMISSION_REQUIRED,
    authenticated_userid,
    Authenticated,
)
from pyramid.httpexceptions import HTTPFound

from urlparse import urlparse, parse_qsl, ParseResult
from urllib import urlencode

from pyramid_oauth2_provider.views import require_https, add_cache_headers
from pyramid_oauth2_provider.errors import InvalidToken, InvalidClient, InvalidRequest, UnsupportedGrantType
from pyramid_oauth2_provider.util import oauth2_settings, getClientCredentials
from pyramid_oauth2_provider.interfaces import IAuthCheck
from pyramid_oauth2_provider.jsonerrors import HTTPBadRequest, HTTPUnauthorized, HTTPMethodNotAllowed

from pyramid_oauth2_provider.generators import gen_token

from pyuserdb.cassandra_.models import (
    OAuth2Client,
    OAuth2AuthorizationGrant,
    OAuth2AccessToken,
    OAuth2RefreshToken,
)


log = logging.getLogger('gpyramid_oauth2.views')


def handle_base_authorize_request(request):
    """
    Provide basic validatation of incoming authorize request.

    :param pyramid.request.Request request: Incoming Web Request

    :return: Validated OAuth2 Client record
    :rtype: pyuserdb.cassandra_.OAuth2Client
    """
    request.client_id = request.params.get('client_id')

    cdb_session = request.cdb_session
    try:
        client = OAuth2Client.get(client_id=request.client_id)

    except OAuth2Client.DoesNotExist:
        log.info('received invalid client credentials')
        raise HTTPBadRequest(InvalidRequest(
            error_description='Invalid client credentials'))

    redirect_uri = request.params.get('redirect_uri')
    redirection_uri = None
    if len(client.redirect_uris) == 1 and (
        not redirect_uri or redirect_uri == client.redirect_uris[0]):
        redirection_uri = client.redirect_uris[0]
    elif len(client.redirect_uris) > 0:
        for i in client.redirect_uris:
            if redirect_uri == i:
                redirection_uri = redirect_uri
                break

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

    if redirection_uri is None:
        return HTTPBadRequest(InvalidRequest(
            error_description='Redirection URI validation failed'))

    state = request.params.get('state')
    resp = handle_authcode(request, client, redirection_uri, state)
    return resp


@view_config(
    route_name='oauth2_provider_authorize',
    renderer='json',
    request_param='response_type=token',
    permission=NO_PERMISSION_REQUIRED,
)
@require_https
def oauth2_authorize_token(request):
    client, redirection_uri = handle_base_authorize_request(request)

    if redirection_uri is None:
        return HTTPBadRequest(InvalidRequest(
            error_description='Redirection URI validation failed'))

    state = request.params.get('state')
    resp = handle_implicit(request, client, redirection_uri, state)
    return resp


@view_config(
    route_name='oauth2_provider_authorize',
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
    log.info('received invalid response_type %s')
    resp = HTTPBadRequest(InvalidRequest(error_description='Oauth2 unknown '
        'response_type not supported'))

    return resp


def handle_authcode(request, client, redirection_uri, state=None):
    """
    Setup an authorization code session.

    :param pyramid.request.Request request: Incoming Web Request
    :param pyuserdb.cassandra_.models.OAuth2Client client: OAuth2 Client Record
    :param str redirection_uri: redirection URI associated with client
    :param str | None state: optional state string

    :return:
    """
    parts = urlparse(redirection_uri)
    qparams = dict(parse_qsl(parts.query))

    user_id = authenticated_userid(request)

    auth_code = OAuth2AuthorizationGrant.create(
        client_id=client.client_id,
        user_uuid=user_id,
        authorization_code=gen_token(client),
        valid_until=(datetime.datetime.utcnow() + datetime.timedelta(seconds=60*60)),
    )

    qparams['code'] = auth_code.authorization_code
    if state:
        qparams['state'] = state
    parts = ParseResult(
        parts.scheme, parts.netloc, parts.path, parts.params,
        urlencode(qparams), '')
    return HTTPFound(location=parts.geturl())


def handle_implicit(request, client, redirection_uri, state=None):
    """

    :param pyramid.request.Request request: Incoming Web Request
    :param pyuserdb.cassandra_.models.OAuth2Client client: OAuth2 Client Record
    :param str redirection_uri: redirection URI associated with client
    :param str | None state: optional state string

    :return:
    """
    return HTTPBadRequest(InvalidRequest(error_description='Oauth2 '
        'response_type "implicit" not supported'))


@view_config(
    route_name='oauth2_provider_token',
    renderer='json',
    permission=NO_PERMISSION_REQUIRED
)
@require_https
def oauth2_token(request):
    """
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

    * In the case of a token refresh request a POST with the following
    structure is required:

        POST /token HTTP/1.1
        Host: server.example.com
        Authorization: Basic czZCaGRSa3F0MzpnWDFmQmF0M2JW
        Content-Type: application/x-www-form-urlencoded

        grant_type=refresh_token&refresh_token=tGzv3JOkF0XG5Qx2TlKW&user_id=1234

    The response will be the same as above with a new access_token and
    refresh_token.
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

    cdb_session = request.cdb_session
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
    resp = None
    grant_type = request.POST.get('grant_type')
    if grant_type == 'password':
        resp = handle_password(request, client)

    elif grant_type == 'refresh_token':
        resp = handle_refresh_token(request, client)

    else:
        log.info('invalid grant type: %s' % grant_type)
        return HTTPBadRequest(UnsupportedGrantType(error_description='Only '
            'password and refresh_token grant types are supported by this '
            'authentication server'))

    add_cache_headers(request)
    return resp


def token_as_json(refresh_token, expires_in, **kwargs):
    """

    :param pyuserdb.cassandra_.models.OAuth2RefreshToken refresh_token: Pending RefreshToken
    :param int expires_in: Number of seconds until token expires
    :param dict kwargs: Addtional keyword arguments to add to resulting dict.

    :return:
    """
    token = {
        'access_token': refresh_token.access_token,
        'refresh_token': refresh_token.refresh_token,
        'user_id': refresh_token.user_uuid,
        'expires_in': expires_in,
    }
    kwargs.update(token)
    return kwargs


def create_token_set(client, user_uuid):
    """

    :param pyuserdb.cassandra_.models.OAuth2Client client: OAuth2 Client
    :param str user_uuid: User UUID
    :return:
    """

    access_token = OAuth2AccessToken.create(
        access_token=gen_token(client),
        user_uuid=user_uuid,
        client_id=client.client_id,
        valid_until=0,
    )
    refresh_token = OAuth2RefreshToken.create(
        refresh_token=gen_token(client),
        access_token=access_token.access_token,
        user_uuid=access_token.user_uuid,
        client_id=access_token.client_id,
        valid_until=0,
    )

    return access_token, refresh_token


def handle_password(request, client):
    """

    :param pyramid.request.Request request: Incoming Web Request
    :param pyuserdb.cassandra_.models.OAuth2Client client: OAuth2 Client

    :return:
    """
    if 'username' not in request.POST or 'password' not in request.POST:
        log.info('missing username or password')
        return HTTPBadRequest(InvalidRequest(error_description='Both username '
            'and password are required to obtain a password based grant.'))

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


def handle_refresh_token(request, client):
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
        refresh_token = OAuth2RefreshToken.get(refresh_token=request.POST.get('refresh_token'))

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
        OAuth2AccessToken.get(access_token=refresh_token.access_token).delete()

    except OAuth2AccessToken.DoesNotExist:
        pass

    new_access_token, new_refresh_token = create_token_set(client, refresh_token.user_uuid)
    refresh_token.delete()

    expires_in = new_access_token.valid_until
    return token_as_json(new_refresh_token, expires_in, token_type='bearer')
