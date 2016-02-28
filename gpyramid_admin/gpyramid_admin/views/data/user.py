#
import uuid
import functools

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPOk, HTTPNotFound

from paginate import Page

from cassandra.cqlengine.query import LWTException  # , BatchQuery

from pyuserdb.cassandra_.models import User, AuthenticationUser

from gpyramid_admin.utils.paginate import PageURL_WebOb, PageCollection_CassandraCQLEngine
import gpyramid_admin.forms.data.user as user_forms


ITEMS_PER_PAGE = 10


@view_config(
    route_name='data.user.list_or_create',
    renderer='data/user_list.html.mako',
    request_method=('POST', 'GET'),
)
def user_list(request):
    """
    :param pyramid.request.Request request: Incoming Web Request
    """
    try:
        page_num = int(request.params.get('page', 1))
        if page_num < 1:
            page_num = 1

    except ValueError:
        page_num = 1
    try:
        items_per_page = int(request.params.get('per_page', ITEMS_PER_PAGE))
        if items_per_page < 1:
            items_per_page = 1

    except ValueError:
        items_per_page = ITEMS_PER_PAGE

    # Enable cassandra connection
    csdb_session = request.csdb_session

    if request.method == 'POST':
        form = user_forms.CreateUserForm(request.POST)
        if form.validate():

            try:
                auth_user = AuthenticationUser.get(username=form.username.data)

                # record found, Username is taken, need to mark this as an error.
                form.error_username_in_use()

            except AuthenticationUser.DoesNotExist:
                # Good, username not taken yet.
                user = User(
                    user_uuid=form.user_uuid.data.lower() or uuid.uuid4(),
                    username=form.username.data.lower(),
                    password=form.password.data,
                    first_name=form.first_name.data or '',
                    last_name=form.last_name.data,
                    display_name=form.display_name.data or u'{0} {1}'.format(
                        form.first_name.data, form.last_name.data).strip(),
                    email=form.email.data,
                )
                auth_user = AuthenticationUser(
                    username=user.username,
                    password=user.password,
                    user_uuid=user.user_uuid,
                )

                # Need to manually track transaction of record insertion.
                # TODO: Should force the datacenter in use to be consistent for application inserts.
                # Validate username first
                try:
                    auth_user.if_not_exists(True).save()

                except LWTException:
                    # Username taken
                    form.error_username_in_use()

                else:
                    # Need to determine if we can auto generate a new UUID in case of failure, or need to flag error.
                    if form.user_uuid.data:
                        # Specified UUID
                        try:
                            user.if_not_exists(True).save()

                            # Records inserted without issue. Good to go.
                            return HTTPFound(
                                location=request.route_path('data.user.list_or_create')
                            )

                        except LWTException:
                            # Username taken
                            form.error_user_uuid_in_use()

                            # Need to backout authentication record
                            auth_user.delete()

                    else:
                        # Randomly allocated, try X times. Should never happen \u1F91E
                        for i in xrange(10):
                            try:
                                user.if_not_exists(True).save()

                                # Records inserted without issue. update authentication record in case UUID changed.
                                auth_user.user_uuid = user.user_uuid
                                auth_user.save()

                                return HTTPFound(
                                    location=request.route_path('data.user.list_or_create')
                                )

                            except LWTException:
                                # UUID conflict, allocate a new one and try again.
                                user.user_uuid = uuid.uuid4()

                            # Else,
                            # Username taken
                            form.user_uuid.data = user.user_uuid
                            form.error_user_uuid_in_use()

                            # Need to backout authentication record
                            auth_user.delete()

                # try:
                #     # Light Weight Transaction across multiple inserts.
                #     # TODO: Should force the datacenter in use to be consistent for application inserts.
                #     with BatchQuery() as b:
                #         user.batch(b).if_not_exists(True).save()
                #         auth_user.batch(b).if_not_exists(True).save()
                #
                #     return HTTPFound(
                #         location=request.route_path('data.user.list_or_create')
                #     )
                #
                # except LWTException:
                #     # User UUID or username in use.
                #     form.error_username_in_use()

        # Else, form errors

    else:  # request.method = 'GET'
        form = user_forms.CreateUserForm()

    # TODO: Paginators like to know maximum limit, not very nice in cassandra.
    # TODO: Need to validate page number since paginator does not do a good job.
    paginator = Page(
        User.objects,
        page_num,
        url_maker=PageURL_WebOb(request),
        items_per_page=items_per_page,
        wrapper_class=functools.partial(PageCollection_CassandraCQLEngine, items_per_page),
    )

    return {
        'request': request,
        'page_num': page_num,
        'items_per_page': items_per_page,
        'paginator': paginator,
        'form': form,
    }


@view_config(
    route_name='data.user.view_or_edit',
    renderer='data/user_view.html.mako',
    request_method=('POST', 'GET'),
)
def user_view(request):
    """
    :param pyramid.request.Request request: Incoming Web Request
    """
    user_uuid = request.matchdict['user_uuid']

    # Enable cassandra connection
    csdb_session = request.csdb_session

    try:
        user = User.get(user_uuid=user_uuid)

    except User.DoesNotExist:
        raise HTTPNotFound

    if request.method == 'POST':
        form = user_forms.EditUserForm(request.POST)
        if form.validate():
            # Update Authentication information if necessary.
            if user.username != form.username.data:
                # Changed username, this is a major change in authentication table. Need to create and delete entries.
                # TODO: Need to check that username not already in use.
                AuthenticationUser.create(
                    username=form.username.data,
                    password=form.password.data or user.password,
                    user_uuid=user.user_uuid,
                )
                AuthenticationUser.get(username=user.username).delete()

            elif form.password.data:
                # Update password in existing authentication record
                auth = AuthenticationUser.get(username=user.username)
                auth.update(password=form.password.data)

            # Populate fields to update in user record. Skip optional fields with empty strings.
            kwargs = {
                key: value
                for key, value in form.data.items()
                if value or (form[key].flags.optional and user[key] != value)
            }
            kwargs.pop('confirm_password', None)
            user.update(**kwargs)

            return HTTPFound(
                location=request.route_path('data.user.view_or_edit', user_uuid=user_uuid)
            )

        # Else, form errors

    else:  # request.method = 'GET'
        form = user_forms.EditUserForm()

        form.username.data = user.username
        form.email.data = user.email
        form.first_name.data = user.first_name
        form.last_name.data = user.last_name
        form.display_name.data = user.display_name

    return {
        'request': request,
        'user': user,
        'form': form,
    }


@view_config(
    route_name='data.user.view_or_edit',
    request_method='DELETE',
)
def user_delete(request):
    """
    :param pyramid.request.Request request: Incoming Web Request
    """
    user_uuid = request.matchdict['user_uuid']

    # Enable cassandra connection
    csdb_session = request.csdb_session

    try:
        user = User.get(user_uuid=user_uuid)

    except User.DoesNotExist:
        raise HTTPNotFound

    user.delete()

    return HTTPOk()
