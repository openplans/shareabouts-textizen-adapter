# Allow all traffic to be forwarded to https
forwarded_allow_ips = '*'
x_forwarded_for_header = 'X-FORWARDED-FOR'
secure_scheme_headers = {
    'X-FORWARDED-PROTO': 'https',
}

# Use gevent, if available
try:
    import gevent
except ImportError:
    worker_class = 'sync'
else:
    worker_class = 'gevent'
