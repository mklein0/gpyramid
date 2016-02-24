#
from zope.interface import implementer

from pyramid.interfaces import IAuthenticationPolicy, IAuthorizationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from pyramid_oauth2_provider.interfaces import IAuthCheck

from gpyramid_oauth2.authentication import OauthAuthenticationPolicy

from pyuserdb.cassandra_.models import (
    AuthenticationUser,
)


@implementer(IAuthCheck)
class UserCredentialAuthenticationPolicy(object):

    def checkauth(self, username, password):
        """
        Validate a given username and password against some kind of store,
        usually a relational database. Return the users user_id if credentials
        are valid, otherwise False or None.

        :param str username: Username of User
        :param str password: Password for User

        :rtype: uuid.UUID
        """
        try:
            user_auth = AuthenticationUser.get(username=username)

        except AuthenticationUser.DoesNotExist:
            # No user by that username
            return None

        if password != user_auth.password:
            # Passwords did not match
            return None

        return user_auth.user_uuid


def includeme(config):
    """

    :param pyramid.config.Configurator config: Pyramid WGSI configuration
    """

    # http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/security.html
    if not config.registry.queryUtility(IAuthenticationPolicy):
        config.set_authentication_policy(OauthAuthenticationPolicy())

    if not config.registry.queryUtility(IAuthorizationPolicy):
        config.set_authorization_policy(ACLAuthorizationPolicy())



    config.registry.registerUtility(UserCredentialAuthenticationPolicy, IAuthCheck)