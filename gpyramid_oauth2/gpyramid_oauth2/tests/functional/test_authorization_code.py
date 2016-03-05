#
import urlparse
import base64

from gpyramid_oauth2.tests.functional.util import BaseAppFunctionalTestCase


class AuthorizationCodeAuthorizeFunctionalTestCase(BaseAppFunctionalTestCase):

    def test_simple_request(self):

        # Make initial authorize call for implicit token
        params = dict(
            response_type='code',
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
        )

        rsp = self.testapp.get('/oauth2/authorize', params=params)
        self.assertEqual(rsp.status_int, 302)

        login_page = self.testapp.get(rsp.location)

        # Fill in login form.
        login_page.form.fields['username'][0].value = 'firstuser'
        login_page.form.fields['password'][0].value = 'testtest'

        login_rsp = login_page.form.submit()
        self.assertEqual(login_rsp.status_int, 302)

        completion_rsp = self.testapp.get(login_rsp.location)
        self.assertEqual(completion_rsp.status_int, 302)

        redirect_parts = urlparse.urlparse(self.redirect_uri)
        url_parts = urlparse.urlparse(completion_rsp.location)
        self.assertEqual(url_parts.scheme, redirect_parts.scheme)
        self.assertEqual(url_parts.netloc, redirect_parts.netloc)
        self.assertEqual(url_parts.path, redirect_parts.path)
        self.assertEqual(url_parts.params, redirect_parts.params)
        self.assertNotEqual(url_parts.query, '')
        self.assertEqual(url_parts.fragment, redirect_parts.fragment)

        qstr = urlparse.parse_qs(url_parts.query)
        self.assertIn('code', qstr)
        self.assertEqual(len(qstr['code']), 1)

        # self.assertIn('expires_in', fragments)
        # self.assertIn('token_type', fragments)
        # self.assertEqual(len(fragments['token_type']), 1)
        # self.assertEqual(fragments['token_type'][0], 'bearer')
        # self.assertNotIn('state', fragments)

        basic_auth = 'Basic {0}'.format(
            base64.b64encode(':'.join((self.client_id, self.client_secret))).strip()
        )

        params = dict(
            grant_type='authorization_code',
            code=qstr['code'][0],
            redirect_uri=self.redirect_uri,
        )
        token_rsp = self.testapp.post('/oauth2/token', params=params, extra_environ={
            'HTTP_AUTHORIZATION': basic_auth,
        })
        self.assertEqual(token_rsp.status_int, 200)

        result = token_rsp.json
        fragments = urlparse.parse_qs(url_parts.fragment)
        self.assertIn('access_token', result)
        self.assertIn('expires_in', result)
        self.assertIn('token_type', result)
        self.assertEqual(result['token_type'], 'bearer')
        self.assertIn('refresh_token', result)
        self.assertNotIn('state', fragments)
