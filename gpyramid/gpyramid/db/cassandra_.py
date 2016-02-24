#
"""
Integrate Cassandra DB session with pyramid request object.
"""
from itertools import islice

from cassandra.cluster import Cluster
from cassandra.cqlengine import connection


def decode_settings_key(settings, key):
    """
    :param pyramid.config.configurator.Settings settings: Pyramid Settings for application
    :param str key: Dot separated key name values

    :rtype: Any
    """
    empty_dict = {}
    result = settings
    key_values = key.split('.')
    for key_name in islice(key_values, 0, len(key_values) - 1):
        result = result.get(key_name, empty_dict)

    return result.get(key_values[-1])


def get_cluster_session(request):
    """
    :param pyramid.request.Request request: Incoming Web Request

    :rtype: cassandra.cluster.Session
    """
    settings = request.registry.settings
    kwargs = decode_settings_key(settings, 'cassandra.cluster.new.kwargs')
    cluster = Cluster(**kwargs)

    kwargs = decode_settings_key(settings, 'cassandra.cluster.connect.kwargs')

    return cluster.connect(**kwargs)


def get_cqlengine_session(request):
    """
    :param pyramid.request.Request request: Incoming Web Request

    :rtype: cassandra.cluster.Session
    """

    if connection.session is None:
        settings = request.registry.settings
        kwargs = decode_settings_key(settings, 'cassandra.cqlengine.connection.setup.kwargs')

        # Connect to the demo keyspace on our cluster running at 127.0.0.1
        connection.setup(**kwargs)

    return connection.session


def includeme(config):
    """
    Add a dynamic property to request object to derive Cassandra connection for given request.

    :param pyramid.config.Configurator config: Pyramid Configuration Object
    """
    settings = config.registry.settings
    session_type = decode_settings_key(settings, 'cassandra.session_type') or 'cluster'

    if session_type == 'cqlengine':
        session_func = get_cqlengine_session

    else:  # session_type == 'cluster'
        session_func = get_cluster_session

    config.add_request_method(
        session_func,
        'csdb_session',
        reify=True)