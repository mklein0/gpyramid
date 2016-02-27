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
    password = wtforms.PasswordField(
        'Password', [
            myvalidators.Strip(),
            wtvalidators.InputRequired(),
        ]
    )
    confirm_password = wtforms.PasswordField(
        'Confirm Password', [
            myvalidators.Strip(),
            wtvalidators.EqualTo('password'),
        ]
    )

    first_name = wtforms.StringField(
        'First Name', [
            myvalidators.Strip(),
            wtvalidators.Optional(strip_whitespace=True),
        ]
    )
    last_name = wtforms.StringField(
        'Last Name', [
            myvalidators.Strip(),
            wtvalidators.InputRequired(),
        ]
    )
    display_name = wtforms.StringField(
        'Display Name (Optional)', [
            myvalidators.Strip(),
            wtvalidators.Optional(),
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


class EditUserForm(wtforms.Form):

    username = wtforms.StringField(
        'Username', [
            myvalidators.Strip(),
            wtvalidators.InputRequired(),
        ]
    )
    password = wtforms.PasswordField(
        'Password', [
            myvalidators.Strip(),
            wtvalidators.Optional(),
        ]
    )
    confirm_password = wtforms.PasswordField(
        'Confirm Password', [
            myvalidators.Strip(),
            wtvalidators.EqualTo('password'),
        ]
    )

    first_name = wtforms.StringField(
        'First Name', [
            myvalidators.Strip(),
        ]
    )
    last_name = wtforms.StringField(
        'Last Name', [
            myvalidators.Strip(),
            wtvalidators.InputRequired(),
        ]
    )
    display_name = wtforms.StringField(
        'Display Name', [
            myvalidators.Strip(),
        ]
    )

    email = wtforms.StringField(
        'Email', [
            myvalidators.Strip(),
            wtvalidators.InputRequired(),
            wtvalidators.Email(),
        ]
    )
