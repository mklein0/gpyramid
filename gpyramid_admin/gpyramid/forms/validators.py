#
import wtforms.validators as wtvalidators


class Strip(object):
    """
    Strip whitespace from input data before additional processing.
    """
    def __call__(self, form, field):
        """
        for each value in input data, strip whitespace

        :param wtforms.Form form: Form associated with input processing
        :param wtforms.Field field: Field in Form associated with input processing.
        """
        if field.raw_data:
            field.raw_data = [
                i.strip() if isinstance(i, wtvalidators.string_types) else i
                for i in field.raw_data
            ]


class NoWhiteSpace(wtvalidators.Regexp):
    """
    Do not allow any whitespace in input.
    """
    def __init__(self, message=None):
        """
        :param str message: Error message to display if whitespace found.
        """
        if message is None:
            message = 'Whitespace not allowed.'

        super(NoWhiteSpace, self).__init__(r'^\S*', message=message)


class IfXSetThenElse(object):
    """
    Call given validator if another field has data present.
    """
    def __init__(self, fieldname, then_, else_=None):
        """
        :param str fieldname: Name of field in form we are dependent upon.
        :param callable(wtforms.Form, wtforms.Field) then_: Validator to call on given field if value present in another field.
        :param callable(wtforms.Form, wtforms.Field) else_: Validator to call on given field if value not present in another field.
        """
        self.fieldname = fieldname

        self.then_ = then_
        self.else_ = else_

    def __call__(self, form, field):
        """
        Verify the pre-condition of the required field having input is true.
        If the pre-condition field is populated, then the current field is
        required.

        :param wtforms.Form form: Form associated with input processing
        :param wtforms.Field field: Field in Form associated with input processing.
        """
        try:
            precond_field = form[self.fieldname]

        except KeyError:
            raise wtvalidators.ValidationError(
                field.gettext(
                    "Field '{}' not present in form.".format(self.fieldname))
            )

        # Test for existence of values in precondition field.
        if not precond_field.raw_data or not precond_field.raw_data[0]:
            if self.else_ is not None:
                return self.else_(form, field)

        # Else, pre-condition field exists.
        return self.then_(form, field)