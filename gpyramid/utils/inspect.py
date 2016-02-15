#

compat_str = str



def class_to_name(class_type):
    """
    :param object class_type: User Defined Python Class

    :return: A unicode string containing module and class name.
    :rtype: str | unicode
    """
    try:
        class_name = class_type.__name__
    except AttributeError:
        class_name = compat_str(class_name)
    try:
        module_name = class_type.__module__
    except AttributeError:
        module_name = None

    if module_name:
        return compat_str('{}.{}').format(module_name, class_name)

    # Else
    return class_name
