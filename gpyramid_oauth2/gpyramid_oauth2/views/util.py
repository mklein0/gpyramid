import base64
import json


AUTHORIZE_SESSION_COOKIE_NAME = 'gpyramid.auth'
AUTHORIZE_SESSION_TTL = 5 * 60  # 5 Minutes


def save_session(request, response, authorize_value):
    """

    :param pyramid.request.Request request: Incoming Web Request
    :param pyramid.request.Response response: Response to Web Request
    :param dict authorize_value: State to persist

    :rtype: pyramid.request.Response
    """
    serialize_value = base64.b64encode(json.dumps(authorize_value))

    response.set_cookie(
        name=AUTHORIZE_SESSION_COOKIE_NAME,
        value=serialize_value,
        max_age=AUTHORIZE_SESSION_TTL,
        secure=(request.scheme == 'https'),  # For debugging/development reasons
    )
    return response


def load_session(request):
    """

    :param pyramid.request.Request request: Incoming Web Request

    :rtype: dict
    """
    authorize_value = request.cookies.get(AUTHORIZE_SESSION_COOKIE_NAME)
    if authorize_value is None:
        raise ValueError('Cookie Not Found')

    authorize_value = json.loads(base64.b64decode(authorize_value))
    return authorize_value
