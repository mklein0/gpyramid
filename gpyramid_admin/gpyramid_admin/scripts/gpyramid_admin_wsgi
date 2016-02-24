#
"""
"""
import os
from pyramid import paster


def get_wsgi_app(ini_filename='development.ini', app_name='main'):
    """
    This function exists to wrap the setup of the WSGI environment to run
    the application.

    :param str module_name: Name of module containing wsgi
    :param str lib_path: Library path
    :param str ini_filename: Filename of INI file to load for WSGI
    :param str app_name: Application name in INI file.

    :return:
    :rtype:
    """
    ini_realpath = os.path.abspath(ini_filename)
    paster.setup_logging(ini_realpath)

    return paster.get_app(ini_realpath, app_name)


application = get_wsgi_app()
