#
import wtforms
import wtforms.validators as wtvalidators

import gpyramid.forms.validators as myvalidators


class UserLoginForm(wtforms.Form):

    username = wtforms.StringField(
        'Username', [
            myvalidators.Strip(),
            myvalidators.Lowercase(),
            wtvalidators.InputRequired(),
        ]
    )
    password = wtforms.PasswordField(
        'Password', [
            myvalidators.Strip(),
            wtvalidators.InputRequired(),
        ]
    )
    hidden = wtforms.HiddenField()
