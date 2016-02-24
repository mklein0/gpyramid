#

def add_routes(config):
    """
    :param pyramid.config.Configurator config: Pyramid App Config
    """
    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('home', '/')

    # Base login page
    config.add_route('login.page', 'login')

    # OAuth2 End-Points
    config.add_route('oauth2_provider_authorize', 'oauth2/authorize')
    config.add_route('oauth2_provider_token', 'oauth2/token')


def includeme(config):
    """
    :param pyramid.config.Configurator config: Pyramid App Config
    """
    return add_routes(config)
