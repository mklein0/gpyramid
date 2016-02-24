#
from pyramid_configurator.toml import TomlConfigurator as Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

    config.include('pyramid_chameleon')
    config.include('gpyramid_admin.db.cassandra_')
    config.include('gpyramid_admin.routes')

    config.scan()

    return config.make_wsgi_app()
