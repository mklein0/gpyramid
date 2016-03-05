#

def add_routes(config):
    """
    :param pyramid.config.Configurator config: Pyramid App Config
    """
    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('home', '/')

    # Configuration End-Points
    config.add_route('data.index', 'data/')
    config.add_route('data.user.list_or_create', 'data/users/')
    config.add_route('data.user.view_or_edit', 'data/users/{user_uuid:[0-9a-f\-]+}/')
    config.add_route('data.client.list_or_create', 'data/clients/')
    config.add_route('data.client.view_or_edit', 'data/clients/{client_id:[0-9a-f\-]+}/')


def includeme(config):
    """
    :param pyramid.config.Configurator config: Pyramid App Config
    """
    return add_routes(config)
