gpyramid\_oauth2 README
=======================

Overview
--------

This is an example of using a pyramid application with gunicorn and other async WSGI runners.

This also includes some preferred practices in pyramid, such as:
    * Never place application drivers or key functions in \_\_init\_\_.py. The main function is moved to a separate file called main.py.

    1. Setup User via Admin Console
    2. Setup Client via Admin Console
    3. In browser goto:
           http://0.0.0.0:6545/oauth2/authorize?response\_type=code&client\_id=\<client\_id\>
    4. Login
    5. Copy authorization code
    6. Run the following CURL command:
           curl -X POST 'http://0.0.0.0:6545/oauth2/token' \
             --data grant\_type=authorization\_code \
             --data-urlencoded client_id=\<client\_id\> \
             --data-urlencoded code=\<authorization\_code\>
