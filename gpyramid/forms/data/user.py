#
import wtforms
import wtforms.validators as wtvalidators

import gpyramid.forms.validators as myvalidators


class CreateUserForm(wtforms.Form):

    username = wtforms.StringField(
        'Username', [
            myvalidators.Strip(),
            wtvalidators.InputRequired(),
        ]
    )
    email = wtforms.StringField(
        'Email', [
            myvalidators.Strip(),
            wtvalidators.InputRequired(),
            wtvalidators.Email(),
        ]
    )
    user_uuid = wtforms.StringField(
        'UUID (Optional)', [
            myvalidators.Strip(),
            wtvalidators.Optional(),
            wtvalidators.UUID(),
        ]
    )

