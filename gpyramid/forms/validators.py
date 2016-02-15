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


class InputRequiredIfXSet(wtvalidators.InputRequired):
    """
    This input is required if another field has data present.
    """
    def __init__(self, fieldname, message=None):
        """
        :param str fieldname: Name of field in form we are dependent upon.
        :param str message: Error message to display if field required and not present.
        """
        super(InputRequiredIfXSet, self).__init__(message=message)

        self.fieldname = fieldname

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

        try:
            super(InputRequiredIfXSet, self).__call__(form, precond_field)
            
        except wtvalidation.ValidationError:
            # No value present
            return

        # Required precondition field is present, check current field.
        return super(InputRequiredIfXSet, self).__call__(form, field)
