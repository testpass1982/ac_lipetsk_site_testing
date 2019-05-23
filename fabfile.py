from fabric.api import *
from fabric.contrib import files
from fabric.contrib.files import exists
from fabric.colors import green, red
import time
import json

# env.use_ssh_config = False
# env.disable_known_hosts = True
# from fabric import Connection
# https://micropyramid.com/blog/automate-django-deployments-with-fabfile/

try:
    with open("secret.json") as secret_file:
        secret = json.load(secret_file)
        env.update(secret)
        # env.hosts = secret['hosts']
except FileNotFoundError:
    print('***ERROR: no secret file***')

env.use_ssh_config = True
env.hosts = ['server']

def test():
    # get_secret()
    run('ls -la')
    run('uname -a')

def backup():
    print(green('pulling remote repo...'))
    local('git pull')
    print(green('adding all changes to repo...'))
    local('git add .')
    print(green("enter your comment:"))
    comment = input()
    local('git commit -m "{}"'.format(comment))
    print(green('pushing master...'))
    local('git push -u origin master')

def migrate():
    local('python3 manage.py makemigrations')
    local('python3 manage.py migrate')

def check_exists(filename):
    if files.exists(filename):
        print(green('YES {} exists!'.format(filename)))
        return True
    else:
        print(red('{} NOT exists!'.format(filename)))
        return False

def test_remote_folder():
    execute(check_exists, '{}{}'.format(env.path_to_projects, env.project_name))

#as user
def clone():
    print(gree('CLONING...'))
    run('git clone https://github.com/testpass1982/{}.git'.format(env.project_name))

#as user
def update():
    print(green('UPDATING...'))
    run('git pull')

#as user
def make_configs():
    local("sed 's/PROJECT_NAME/{}/g; \
                s/DOMAIN_NAME/{}/g; \
                s/USERNAME/{}/g' \
            nginx_config_template > {}_nginx".format(
        env.project_name, env.domain_name, env.user, env.project_name))
    print(green('***NGINX CONFIG READY***'))
    local("sed 's/PROJECT_NAME/{}/g; \
                s/USERNAME/{}/g' \
            systemd_config_template > {}.service".format(
        env.project_name, env.domain_name, env.user, env.project_name))
    print(green('***SYSTEMD CONFIG READY***'))
    print(green("""
************************
****CONFIGS COMPLETE****
************************
    """))

#as sudo
def copy_systemd_config():
    run('cp {}.service /etc/systemd/system/{}.service'.format(env.project_name))
    run('cd /etc/systemd/system/')
    run('systemctl enable {}.service'.format(env.project_name))
    run('systemctl start {}.service'.format(env.project_name))

#as sudo
def copy_nginx_config():
    print(green('checking nginx-configuration'))
    # put('{}_nginx'.format(env.project_name), '/etc/nginx/sites-available/{}_nginx'.format(env.project_name), use_sudo=True)
    if not exists('/etc/nginx/sites-available/{}_nginx'.format(env.project_name), use_sudo=True):
        put('{}_nginx'.format(env.project_name), '/home/{}/'.format(env.user))
        sudo('mv /home/{}/{}_nginx /etc/nginx/sites-available/'.format(env.user, env.project_name))
        sudo('nginx -t')
        sudo('ln -s /etc/nginx/sites-available/{} /etc/nginx/sites-enabled/'.format(env.project_name))
        sudo('nginx -s reload')
    else:
        print(red('nginx configuration for project {} exists'.format(env.project_name)))

def copy_systemd_config():
    print(green('checking systemd-configuration'))
    if not exists('/etc/systemd/system/{}.service'.format(env.project_name)):
        put('{}.service'.format(env.project_name), '/home/{}'.format(env.user))
        sudo('mv /home/{}/{}.service /etc/systemd/system/'.format(env.user, env.project_name))
        sudo('systemctl enable {}.service'.format(env.project_name))
        sudo('systemctl start {}.service'.format(env.project_name))
        sudo('systemctl status {}.service'.format(env.project_name))
    else:
        print(red('systemd {}.service already exists'.format(env.project_name)))

def deploy():
    local('git pull')
    local("python3 manage.py test")
    local('pip freeze > requirements.txt')
    # local('git add -p && git commit')
    # print(green("enter your comment:"))
    # comment = input()
    c_time = time.ctime()
    local('git add .')
    local('git commit -m "deploy on {}"'.format(c_time))
    local('git push -u origin master')
    #switch_debug("True", "False")
    local('python3 manage.py collectstatic --noinput')
    print(green('***Executing on {} as {}***'.format(unv.hosts, env.user)))
    #switch_debug("False", "True")