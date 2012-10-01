#!/bin/bash

export PYTHONPATH=gen/py:gen/py/debug/jdwp:gen/py/google
exec ./gen/py/test/test_server.py
