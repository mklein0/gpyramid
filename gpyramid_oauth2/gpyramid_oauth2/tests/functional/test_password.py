#
import base64

from gpyramid_oauth2.tests.functional.util import BaseAppFunctionalTestCase


class ResourceOwnerPasswordCredentialTokenFunctionalTestCase(BaseAppFunctionalTestCase):

    def test_simple_request(self):

        # Make initial authorize call for implicit token
        basic_auth = 'Basic {0}'.format(
            base64.b64encode(':'.join((self.client_id, self.client_secret))).strip()
        )

        params = dict(
            grant_type='password',
            username='firstuser',
            password='testtest',
        )
        token_rsp = self.testapp.post('/oauth2/token', params=params, extra_environ={
            'HTTP_AUTHORIZATION': basic_auth,
        })
        self.assertEqual(token_rsp.status_int, 200)

        result = token_rsp.json
        self.assertIn('access_token', result)
        self.assertIn('expires_in', result)
        self.assertIn('token_type', result)
        self.assertEqual(result['token_type'], 'bearer')
        self.assertIn('refresh_token', result)
        self.assertNotIn('state', result)
