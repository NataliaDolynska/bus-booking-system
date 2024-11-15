# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

bind = '0.0.0.0:443'  # Use port 443 for HTTPS
workers = 1
accesslog = '-'
loglevel = 'debug'
capture_output = True
enable_stdio_inheritance = True

# SSL Configuration
ssl_certfile = 'localhost.crt'  # Replace with the correct path to your SSL certificate
ssl_keyfile = 'localhost.key'