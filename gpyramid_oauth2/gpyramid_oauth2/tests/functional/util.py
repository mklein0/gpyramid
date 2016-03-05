#
import unittest

from webtest import TestApp


class PyramidBaseFunctionalTestCase(unittest.TestCase):

    def get_wsgi_application(self):  # pragma: no cover
        raise NotImplementedError

    def setUp(self):
        self.testapp = TestApp(self.get_wsgi_application())


class BaseAppFunctionalTestCase(PyramidBaseFunctionalTestCase):

    client_id = '349c3eb2-a400-4df3-b381-ebe2e222d6c8'
    client_secret = '824276e8-f727-4840-b69f-9da36b20eae6'
    redirect_uri = 'http://localhost/redirect'

    def get_wsgi_application(self):
        from gpyramid_oauth2.main import main
        settings = {
            'oauth2_provider.require_ssl': 'false',
            'pyramid.includes': 'pyramid_mako',
            'mako.directories': 'gpyramid_oauth2:templates',
            'cassandra': dict(
                session_type='cqlengine',
                cqlengine=dict(
                    connection=dict(
                        setup=dict(
                            kwargs=dict(
                                hosts=['127.0.0.1'],
                                default_keyspace='pyuserdb',
                                protocol_version=3,
                            ),
                        ),
                    ),
                ),
            ),
        }

        return main({}, **settings)
