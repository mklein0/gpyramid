#
import wtforms
import wtforms.validators as wtvalidators

import gpyramid.forms.validators as myvalidators


class CreateClientForm(wtforms.Form):

    client_id = wtforms.StringField(
        'Client ID (Optional)', [
            myvalidators.Strip(),
            wtvalidators.Optional(),
            wtvalidators.UUID(),
        ]
    )

    client_secret = wtforms.StringField(
        'Client Secret (Optional)', [
            myvalidators.Strip(),
            wtvalidators.Optional(),
            wtvalidators.UUID(),
        ]
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
            wtvalidators.URL(),
        ]
    )

