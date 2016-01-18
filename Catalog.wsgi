#!/usr/bin/python
import os, sys
import logging

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/var/www/Catalog/")
sys.path.insert(1, "/var/www/Catalog/Catalog/")


from project import app as application
application.secret_key = 'string'
