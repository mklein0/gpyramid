#
import wtforms
import wtforms.validators as wtvalidators

import gpyramid.forms.validators as myvalidators


class CreateClientForm(wtforms.Form):

    name = wtforms.StringField(
        'Name', [
            myvalidators.Strip(),
            wtvalidators.InputRequired(),
        ]
    )

    client_type = wtforms.SelectField(
        'Client Type', [
            wtvalidators.InputRequired(),
        ],
        choices=(
            ('mobile', 'Mobile'),
            ('web-server', 'Web Server'),
        )
    )

    email = wtforms.StringField(
        'Email', [
            myvalidators.Strip(),
            wtvalidators.InputRequired(),
            wtvalidators.Email(),
        ]
    )

    redirect_uri = wtforms.StringField(
        'Redirect URI', [
            myvalidators.Strip(),
            wtvalidators.InputRequired(),
            wtvalidators.URL(require_tld=False),
        ]
    )

    home_page = wtforms.StringField(
        'Home Page URI (Optional)', [
            myvalidators.Strip(),
            wtvalidators.Optional(),
            wtvalidators.URL(require_tld=False),
        ]
    )

    client_id = wtforms.StringField(
        'Client ID (Optional)', [
            myvalidators.Strip(),
            wtvalidators.Optional(),
            myvalidators.NoWhiteSpace(),
        ]
    )

    client_secret = wtforms.StringField(
        'Client Secret (Optional)', [
            myvalidators.Strip(),
            wtvalidators.Optional(),
            myvalidators.NoWhiteSpace(),
        ]
    )

    def error_client_id_in_use(self):
        """
        Mark the form with a username denoting the username is already in use.
        """
        self._error = None
        self.client_id.process_errors = self.client_id.errors = [
            ValueError('Username already in use')
        ]


class EditClientForm(wtforms.Form):

    client_secret = wtforms.StringField(
        'Client Secret', [
            myvalidators.Strip(),
            wtvalidators.InputRequired(),
            myvalidators.NoWhiteSpace(),
        ]
    )

    name = wtforms.StringField(
        'Name', [
            myvalidators.Strip(),
            wtvalidators.InputRequired(),
        ]
    )

    client_type = wtforms.SelectField(
        'Client Type', [
            wtvalidators.InputRequired(),
        ],
        choices=(
            ('mobile', 'Mobile'),
            ('web-server', 'Web Server'),
        )
    )

    email = wtforms.StringField(
        'Email', [
            myvalidators.Strip(),
            wtvalidators.InputRequired(),
            wtvalidators.Email(),
        ]
    )

    redirect_uri = wtforms.StringField(
        'Redirect URI', [
            myvalidators.Strip(),
            wtvalidators.InputRequired(),
            wtvalidators.URL(require_tld=False),
        ]
    )

    home_page = wtforms.StringField(
        'Home Page URI (Optional)', [
            myvalidators.Strip(),
            wtvalidators.Optional(),
            wtvalidators.URL(require_tld=False),
        ]
    )
