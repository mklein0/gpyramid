import base64
import json


class OAuth2AuthorizeSession(dict):

    AUTHORIZE_SESSION_COOKIE_NAME = 'gpyramid.auth'
    AUTHORIZE_SESSION_TTL = 5 * 60  # 5 Minutes

    def __init__(self, request, response=None, secure=None):
        """
        :param pyramid.request.Request request: Incoming Web Request
        """
        super(OAuth2AuthorizeSession, self).__init__()

        self.request = request
        self.response = response or request.response
        self.secure = secure

    def set_response(self, response):
        self.response = response

    def set_user_id(self, user_id):
        """

        :param str user_id: User ID to add to session

        :return:
        :rtype: OAuth2AuthorizeSession
        """

        self['user_uuid'] = user_id
        return self

    def save(self):
        serialize_value = base64.b64encode(json.dumps(self))
        secure = self.secure if self.secure is not None else (self.request.scheme == 'https')

        self.response.set_cookie(
            name=self.AUTHORIZE_SESSION_COOKIE_NAME,
            value=serialize_value,
            max_age=self.AUTHORIZE_SESSION_TTL,
            secure=secure,
        )

    def _load(self):
        authorize_value = self.request.cookies.get(self.AUTHORIZE_SESSION_COOKIE_NAME)
        if authorize_value is None:
            raise ValueError('Cookie Not Found')  # pragma: no cover

        authorize_value = json.loads(base64.b64decode(authorize_value))
        self.update(authorize_value)

    @classmethod
    def load(cls, request):
        """

        :param pyramid.request.Request request: Incoming Web Request

        :return: Load Authorize session associated Web Request.
        :rtype: OAuth2AuthorizeSession
        """
        session = cls(request)
        session._load()
        return session
