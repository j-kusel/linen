from fabric.api import abort, cd, env, lcd, local, prefix, run, settings, sudo
from fabric.contrib import project
from fabric.contrib.console import confirm
from fabric.contrib.files import append, exists, sed
from fabric.decorators import roles
from contextlib import contextmanager as _contextmanager
from linen.config import LinenSettings as LS
from linen.templates import TempManager
import os, re, random

env.roledefs.update({
    'local': 'localhost',
    'webserver': APACHE_HOSTS,
    'dbserver': MYSQL_HOSTS,
    'mediaserver': MEDIA_HOSTS,
})

env.user = 'jordankusel'

projname = os.path.dirname(os.getcwd())

def printproj():
    print(projname)

#env.directory = pathname
env.proj = projname
env.venv = VIRTUALENV
env.deploy_dir = '/srv/www/{}'.format(env.proj)
env.venv_dir = '{}/{}'.format(env.deploy_dir, env.venv)
env.apache_dir = '/etc/apache2'

env.colorize_errors = True

apps = [
    'blog',
    'projects',
]

local_shell = '/bin/bash'

@_contextmanager
def virtualenv(source):
    with cd(source):
        with prefix('. ../{}/bin/activate'.format(env.venv)):
            yield

def hello():
    print('hello world')

@roles('local')
def new_templates():
    """moves linfile.py and passwords.py templates to current directory"""
    TempManager.mv(os.getcwd)

def migrate():
    _create_directory_structure_if_necessary()
    _config_packages()
    _install_git()
    env.source_folder = env.deploy_dir + '/source'
    _pull_source(env.source_folder)
    _update_settings(env.source_folder)
    _config_mysql()
    _config_apache()
    _update_virtualenv(env.source_folder)
    _update_database(env.source_folder)

    local_manage = os.path.dirname(path.realpath(__file__))
    _migrate_static(env.source_folder)
    _create_superuser(env.source_folder)

def update():
    env.source_folder = env.deploy_dir + '/source'
    _fetch_git(env.source_folder)
    _update_database(env.source_folder)
    _migrate_static(env.source_folder)
    _restart_apache()

@roles('webserver')
def _fetch_git(source):
    if exists(source + '/.git'):
        with cd(source):
            sudo('git pull && git checkout {}'.format(REPO_BRANCH))

@roles('webserver')
def _restart_apache():
    sudo('apache2ctl restart')

@roles('webserver')
def _create_directory_structure_if_necessary():
    sudo('mkdir -p {}'.format(env.deploy_dir))
    for subfolder in ('static', 'media', env.venv, 'source'):
        sudo('mkdir -p {}/{}'.format(env.deploy_dir, subfolder))

@roles('webserver')
def _install_git():
    sudo('apt-get -y install git-core && git config --global user.name "{}" && git config --global user.email {}'.format(ADMIN_INFO['name'], ADMIN_INFO['email']))

@roles('webserver')
def _pull_source(source):
    sudo('git clone {} --branch {} --single-branch {}'.format(REPO_URL, REPO_BRANCH, source))

    # CHECK LOCAL COMMIT
    current_commit = local('git log -n 1 --format=%H', capture=True)
    # HARD RESET SERVER CODE
    run('cd {} && git reset --hard {}'.format(source, current_commit))

@roles('webserver')
def _update_settings(source):
    settings_path = '{}/{}/settings.py'.format(source, env.proj)
    sudo('mv {}/{}/settings_deploy.py {}'.format(source, env.proj, settings_path))

    # TURN OFF DEBUG MODE
    sed(settings_path, "DEBUG.*$", "DEBUG = False", use_sudo=True)

    # CHANGE ALLOWED HOSTS
    hosts = APACHE_HOSTS
    hosts.append(DOMAIN_NAMES)
    hoststr = '", "'.join(hosts)
    sed(settings_path,
        'ALLOWED_HOSTS =.+$',
        'ALLOWED_HOSTS = ["%s"]' % (hoststr),
        use_sudo=True
    )

    # CHANGE STATIC_ROOT / MEDIA_ROOT PATHS
    run(r"sudo sed -i.bak -r -e 's/STATIC_ROOT =.*$/STATIC_ROOT = os.path.join(BASE_DIR, '\''..\/static'\'')/g' {}".format(settings_path))
    append(settings_path, "MEDIA_URL = '/media/'", use_sudo=True)
    append(settings_path, "MEDIA_ROOT = os.path.join(BASE_DIR, '../media')", use_sudo=True)

    # INSTALL mod_wsgi.server
    run(r"sudo sed -i.bak -r -e 's/INSTALLED_APPS.*$/INSTALLED_APPS = ['\''mod_wsgi.server'\'',/g' {}".format(settings_path))

    # CHANGE DATABASES
    sql_server = 'localhost' if APACHE_HOST[0] == MYSQL_HOST[0] else MYSQL_HOST[0]
    sudo(r"sed -i.bak -r -e 's/DATABASES = \{/DATABASES = \{'\''default'\'': \{'\''ENGINE'\'': '\''django.db.backends.mysql'\'', '\''NAME'\'': '\''%s_db'\'', '\''USER'\'': '\''%s'\'', '\''PASSWORD'\'': '\''%s'\'', '\''HOST'\'': '\''%s'\'', '\''PORT'\'':'\'''\'',\},/g' %s" % (env.proj, env.user, MYSQLPASS, sql_server, settings_path))

    # GENERATE A NEW KEY (keep key constant after initial deploy)
    secret_key_file = '{}/{}/secret_key.py'.format(source, env.proj)
    if not exists(secret_key_file):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        key = ''.join(random.SystemRandom().choice(chars) for _ in range(50))
        append(secret_key_file, "SECRET_KEY = '{}'".format(key), use_sudo=True)
    append(settings_path, 'from .secret_key import SECRET_KEY', use_sudo=True)




@roles('webserver')
def _update_virtualenv(source):
    if not exists(env.venv_dir + '/bin/pip'):
        sudo('apt-get -y install python3-pip')
        sudo('pip3 install -U pip')
        sudo('pip3 install virtualenv')
        sudo('virtualenv -p {} {}'.format(PYTHON, env.venv_dir))
    # CHANGE VIRTUALENV OWNERSHIP
    sudo('chown -R {0}:{0} {1}/'.format(env.user, env.venv_dir))

    run('{}/bin/pip install -r {}/requirements.txt'.format(env.venv_dir, source))

@roles('dbserver')
def _config_mysql():

    # BUILD DATABASE, CHANGE PERMISSIONS
    sudo('echo "CREATE DATABASE {}_db;" | mysql --user=root'.format(env.proj))
    sudo("""echo "CREATE USER {0}@{1} IDENTIFIED BY '{2}';" | mysql --user=root""".format(env.user, MYSQL_HOST, MYSQLPASS))
    sudo("""echo "CREATE USER {0} IDENTIFIED BY '{2}';" | mysql --user=root""".format(env.user, MYSQL_HOST, MYSQLPASS))
    sudo("""echo "GRANT ALL ON {0}_db.* TO {1}@{2} IDENTIFIED BY '{3}';" | mysql --user=root""".format(env.proj, env.user, MYSQL_HOST[0], MYSQLPASS))
    sudo("""echo "GRANT ALL ON {0}_db.* TO {1}@localhost IDENTIFIED BY '{2}';" | mysql --user=root""".format(env.proj, env.user, MYSQLPASS))
    sudo("""echo "FLUSH PRIVILEGES;" | mysql --user=root""")

    # CHANGE BIND-ADDRESS
    mysql_conf_path = '/etc/mysql/my.cnf'
    sed(mysql_conf_path, 
        'bind-address.*$',
        'bind-address = {}'.format(APACHE_HOST[0]),
        use_sudo=True)

    # RESTART MYSQL
    sudo('service mysql restart')

@roles('webserver')
def _config_packages():
    # INSTALL PACKAGES
    sudo('apt-get -y update')
    sudo('apt-get -y install python3-pip')
    sudo('apt-get install -y mysql-server && apt-get install -y mysql-client && apt-get -y install libmysqlclient-dev')
    sudo('apt-get -y install apache2')
    sudo('apt-get -y install apache2-dev')
    sudo('apt-get -y install libapache2-mod-wsgi-py3')

    # ENABLE MOD_WSGI
    sudo('a2enmod wsgi')

@roles('webserver')
def _config_apache():
    # MOVE / EDIT CONFIG TEMPLATE FILE (apache.conf)
    apache_config_path = '{}/sites-available/{}.conf'.format(env.apache_dir, env.proj)
    sudo('mv {}/source/apache.conf {}'.format(env.deploy_dir, apache_config_path))

    APACHE_DICT = {
        'SERVERADMIN': ADMIN_INFO['email'],
        'SERVERNAME': DOMAIN_NAMES[0],
        'SERVERROOT': env.deploy_dir,
        'VIRTUALENV': '{}/{}'.format(env.deploy_dir, env.venv),
        'PYTHON': PYTHON,
        'STATICROOT': env.deploy_dir,
        'MEDIAROOT': env.deploy_dir,
        'LOGLEVEL': APACHE_LOGLEVEL,
    }
    
    # add other ServerAliases to APACHE_DICT
    APACHE_DICT['SERVERALIAS'] = ', '.join(DOMAIN_NAMES[1,]) if len(DOMAIN_NAMES) > 1 else DOMAIN_NAMES[0]

    for s in APACHE_DICT:
        sed(apache_config_path, s, APACHE_DICT[s], use_sudo=True)

    # ENABLE SITE
    sudo('a2ensite {}'.format(env.proj))

    # DISABLE DEFAULT HTML PAGE
    sudo('a2dissite 000-default')

    # CHANGE OWNERSHIP TO APACHE
    sudo('chown -R www-data:www-data {}'.format(env.deploy_dir))
    sudo('apache2ctl restart')

@roles('webserver')
def _update_database(source):
    with virtualenv(source):
        run('python3 manage.py makemigrations --noinput')
        run('python3 manage.py migrate --noinput')

def deploy():
    with virtualenv():
        run('git pull')
        with settings(warn_only=True):                
            for a in (apps + ['admin','auth','contenttypes','sessions']):
                run('./manage.py migrate {}'.format(a))

@roles('mediaserver')
def _migrate_static(source):
    # INSTALL RSYNC ON LOCAL AND MEDIA MACHINES
    # local('sudo apt-get -y install rsync')
    # sudo('apt-get -y install rsync')

    # COLLECTSTATIC AND SYNC MEDIA
    # static_new = env.deploy_dir + '/../static/'
    # static = os.path.join(source, 'static/')
    with cd(source):
        sudo('{}/bin/python3 manage.py collectstatic --noinput'.format(env.venv_dir))
    # project.rsync_project(remote_dir=static_new, local_dir=static)

@roles('webserver')
def _create_superuser(source):
    with virtualenv(source):
        run("""echo "from django.contrib.auth.models import User; User.objects.create_superuser('{0}', '{1}', '{2}')" | python3 manage.py shell""".format(SUPERUSER['username'], SUPERUSER['email'], SUPERUSER['password']))
