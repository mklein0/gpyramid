gpyramid_admin README
=====================

Overview
--------

This is an example of using a pyramid application with gunicorn and other async WSGI runners.

This also includes some preferred practices in pyramid, such as:
    * Never place application drivers or key functions in \_\_init\_\_.py. The main function is moved to a separate file called main.py.
