#
import urlparse

from gpyramid_oauth2.tests.functional.util import BaseAppFunctionalTestCase


class ImplicitAuthorizeFunctionalTestCase(BaseAppFunctionalTestCase):

    def test_simple_request(self):

        # Make initial authorize call for implicit token
        params = dict(
            response_type='token',
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
        self.assertEqual(url_parts.query, redirect_parts.query)
        self.assertNotEqual(url_parts.fragment, '')
        fragments = urlparse.parse_qs(url_parts.fragment)
        self.assertIn('access_token', fragments)
        self.assertIn('expires_in', fragments)
        self.assertIn('token_type', fragments)
        self.assertEqual(len(fragments['token_type']), 1)
        self.assertEqual(fragments['token_type'][0], 'bearer')
        self.assertNotIn('refresh_token', fragments)
        self.assertNotIn('state', fragments)

    def test_bad_user_credentials(self):
        # Make initial authorize call for implicit token
        params = dict(
            response_type='token',
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
        )

        rsp = self.testapp.get('/oauth2/authorize', params=params)
        self.assertEqual(rsp.status_int, 302)

        login_page = self.testapp.get(rsp.location)

        # Fill in login form.
        login_page.form.fields['username'][0].value = 'firstuser'
        login_page.form.fields['password'][0].value = 'bad'

        login_rsp = login_page.form.submit()
        self.assertEqual(login_rsp.status_int, 200)
        self.assertIsNotNone(login_rsp.form)
