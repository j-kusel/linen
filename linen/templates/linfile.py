# the location of your remote repository + branch
REPO = {
    'URL': '',
    'BRANCH': '',
}

PYTHON = {
    # version of Python3 in use
    'VERSION': '',

    # desired name of the deployment virtual environment(s)
    'VIRTUALENV': '',

    # directory name of the local virtual environment -
    # it should share a parent directory with the root folder
    # of your Django development site
    'LOCALENV': '',
}

# host IPs (NOTE: currently only supports one at a time)
APACHE_HOSTS = ''
MYSQL_HOSTS = ''
MEDIA_HOSTS = ''

# domain names for Apache that Django will ALLOW
# if DOMAIN_NAMES is a list, the first item will be assigned as ServerName
# and the others will be under ServerAlias
DOMAIN_NAMES = ''

USERS = {

# user for login - goes to env.user
    'DEBIAN_USER': '',

# register Django superuser + MySQL/Apache info
    'SUPERUSER': {
        'name': '',
        'username': '',
        'email': '',
    },

    'MYSQL_INFO': {
        'user': '',
        'name': '',
        'email': '',
    },

    'APACHE_INFO': {
        'user': '',
        'name': '',
        'email': '',

    # verbosity of /var/log/apache2/error.log file
    # options from brief to verbose are:
    # 'emerg', 'alert', 'crit', 'error', 'warn', 'notice', 'info', 'debug'
        'loglevel': 'warn',
    },
}
