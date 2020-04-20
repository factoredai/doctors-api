# doctors-api

## How to deploy

- eb create
- eb setenv `cat .env | sed '/^#/ d' | sed '/^$/ d'`
- In aws console, modify WSGIPath to wsgi.py
