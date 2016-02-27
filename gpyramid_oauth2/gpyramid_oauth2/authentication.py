#
"""
Adaptation of pyramid_oauth2_provider authentication layer for use with Cassandra models.
"""
import logging

from zope.interface import implementer

from pyramid.interfaces import IAuthenticationPolicy
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authentication import CallbackAuthenticationPolicy

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPUnauthorized

from pyramid_oauth2_provider.errors import InvalidToken, InvalidRequest
from pyramid_oauth2_provider.util import getClientCredentials

from pyuserdb.cassandra_.models import (
    OAuth2TokenAccess,
)


log = logging.getLogger('pyramid_oauth2_provider.authentication')

@implementer(IAuthenticationPolicy)
class OauthAuthenticationPolicy(CallbackAuthenticationPolicy):
    def _isOauth(self, request):
        return bool(getClientCredentials(request))

    def _get_auth_token(self, request):
        """

        :param pyramid.request.Request request: Incoming Web Request

        :return: Access token
        :rtype: pyuserdb.cassandra_.OAuth2AccessToken
        """
        token_type, token = getClientCredentials(request)
        if token_type != 'bearer':
            return None

        cdb_session = request.cdb_session
        try:
            access_token = OAuth2TokenAccess.get(access_token=token)

        except OAuth2TokenAccess.DoesNotExist:
            raise HTTPBadRequest(InvalidRequest())

        # # Expired or revoked token, return 401 invalid token
        # if auth_token.isRevoked():
        #     raise HTTPUnauthorized(InvalidToken())

        return access_token

    def unauthenticated_userid(self, request):
        """

        :param pyramid.request.Request request: Incoming Web Request

        :return: User UUID
        """
        auth_token = self._get_auth_token(request)
        if not auth_token:
            return None

        return auth_token.user_uuid

    def remember(self, request, principal, **kw):
        """
        I don't think there is anything to do for an oauth request here.
        """

    def forget(self, request):
        """

        :param pyramid.request.Request request: Incoming Web Request
        """
        auth_token = self._get_auth_token(request)
        if not auth_token:
            return None

        # TODO: revoke token here.
        auth_token.revoke()


@implementer(IAuthenticationPolicy)
class OauthTktAuthenticationPolicy(
        OauthAuthenticationPolicy,
        AuthTktAuthenticationPolicy):

    def __init__(self, *args, **kwargs):
        OauthAuthenticationPolicy.__init__(self)
        AuthTktAuthenticationPolicy.__init__(self, *args, **kwargs)

    def unauthenticated_userid(self, request):
        if self._isOauth(request):
            return OauthAuthenticationPolicy.unauthenticated_userid(
                self, request)
        else:
            return AuthTktAuthenticationPolicy.unauthenticated_userid(
                self, request)

    def remember(self, request, principal, **kw):
        if self._isOauth(request):
            return OauthAuthenticationPolicy.remember(
                self, request, principal, **kw)
        else:
            return AuthTktAuthenticationPolicy.remember(
                self, request, principal, **kw)

    def forget(self, request):
        if self._isOauth(request):
            return OauthAuthenticationPolicy.forget(
                self, request)
        else:
            return AuthTktAuthenticationPolicy.forget(
                self, request)