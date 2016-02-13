#

def add_routes(config):
    """
    :param pyramid.config.Configurator config: Pyramid App Config
    """
    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('home', '/')


def includeme(config):
    """
    :param pyramid.config.Configurator config: Pyramid App Config
    """
    return add_routes(config)
