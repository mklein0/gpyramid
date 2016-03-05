#
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound


# @view_config(route_name='home', renderer='../templates/mytemplate.pt')
# def my_view(request):
#     return {'project': 'gpyramid_admin'}


@view_config(route_name='home.redirect')
def my_view_redirect(request):
    """

    :param pyramid.request.Request request: Incoming Web Request
    """
    return HTTPFound(location=request.route_path('data.index'))