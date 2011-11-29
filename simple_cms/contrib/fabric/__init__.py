import os
import sys
import datetime

from django.conf import settings
from django.core.management import setup_environ, execute_manager
from fabric.api import *
from fabric.contrib.console import confirm

class Deployment(object):
    """
    Base class to handle semi-custom deployment based on Linode stackscript 131
    http://www.linode.com/stackscripts/view/?StackScriptID=131
    
    Server expects pip, virtualenvwrapper
    Default db postgresql
    
    TODO: handle first time deployment
          handle multiple deployment environments
          handle reversion
          handle specific git version deployment
          integrate django-fab-deploy for all database and util operations
    git archive --remote=~/lines.git HEAD | gzip > hot.tgz
    """
    def __init__(self, env, *args, **kwargs):
        self.env = env
        super(Deployment, self).__init__(*args, **kwargs)
    
    def quick_deploy(self):
        self.prepare_local()
        self.prepare_remote()
        self.deploy_code()
        self.finalize_remote()
        self.reload_remote()
        self.cleanup_remote()
        self.cleanup_local()
    
    def deploy(self):
        self.prepare_local()
        self.prepare_remote()
        self.deploy_code()
        self.backup_remote_db()
        self.install_virtualenv()
        self.update_remote_db()
        self.finalize_remote()
        self.restart_webserver()
        self.cleanup_remote()
        self.cleanup_local()
    
    def manual_deploy(self):
        self.prepare_local()
        self.prepare_remote()
        self.deploy_code()
        self.backup_remote_db()
        puts("Code staged, get to steppin")
        open_shell(command='cd %s/d/hot' % self.env['rpath'])
        self.finalize_remote()
        puts("Might want to restart apache.")
        open_shell()
        self.cleanup_remote()
        self.cleanup_local()
    
    def set_remote_environment(self, name):
        pass
    
    def test_local(self):
        local('python manage.py test')
    
    def test_remote(self):
        pass
        
    def prepare_local(self):
        with settings(warn_only=True):
            result = local('git status', capture=False)
            if result.failed and not confirm("Uncommitted changes. Deploy anyway?"):
                abort("Aborting at user request.")
    
    def prepare_remote(self):
        run('mkdir -p %s/d/%s' % (self.env['rpath'], self.env['ms']))
        run('rm -rf %s/d/hot' % self.env['rpath'])
        run('mkdir %s/d/hot' % self.env['rpath'])
    
    def deploy_code(self):
        run('cd %s/d/%s; %s; tar -xzf hot.tgz -C ../hot/' % (self.env['rpath'], self.env['ms'], self.env['create_code_archive']))
        with settings(warn_only=True):
            result = run('cp %s/%s/local_settings.py %s/d/hot/' % (self.env['rpath'], self.env['rpdir'], self.env['rpath']))
    
    def backup_remote_db(self):
        run('pg_dump %s > %s/d/%s/db-%s.sql --user=%s' % (self.env['db_name'], self.env['rpath'], self.env['ms'], self.env['ms'], self.env['db_user']))
    
    def update_remote_db(self):
        with settings(warn_only=True):
            result = run(self.env['workon_remote'] + 'python %s/d/hot/manage.py syncdb' % self.env['rpath'])
            if result.failed and not confirm('Syncdb failed! Continue?'):
                abort('Aborting')
        
        with settings(warn_only=True):
            result = run(self.env['workon_remote'] + 'python %s/d/hot/manage.py migrate' % self.env['rpath'])
            if result.failed and not confirm('Migrate failed! Continue?'):
                abort('Aborting')
    
    def finalize_remote(self):
        with settings(warn_only=True):
            run('rm -rf %s/d/previous' % self.env['rpath'])
            run('mv %s/d/current %s/d/previous' % (self.env['rpath'], self.env['rpath']))
    
        with settings(warn_only=True):
            run('rm -rf %s/d/current' % self.env['rpath'])
    
        run('mv %s/d/hot %s/d/current; rm -rf %s/%s; ln -s %s/d/current %s/%s' %
            (self.env['rpath'], self.env['rpath'], self.env['rpath'], self.env['rpdir'], self.env['rpath'], self.env['rpath'], self.env['rpdir'])
        )
        #symlink uploads, media, static files, etc
        with settings(warn_only=True):
            run('rm -rf %s/public/media' % self.env['rpath'])
            run('ln -s %s/%s/media/ %s/public/media' % (self.env['rpath'], self.env['rpdir'], self.env['rpath']))
            run('ln -s %s/public/uploads/ %s/%s/media/uploads' % (self.env['rpath'], self.env['rpath'], self.env['rpdir']))
            
    def reload_remote(self):
        run('touch %s/python.wsgi' % self.env['rpath'])
    
    def restart_webserver(self):
        sudo('/etc/init.d/apache2 restart')
    
    def cleanup_remote(self):
        pass

    def cleanup_local(self):
        pass
    
    def pull_remote_files(self):
        local('rsync -av %s:%s/public/uploads/ %s/uploads' % (env.host_string, self.env['rpath'], os.path.dirname(__file__)))
    
    def pull_remote_db(self):
        filename = '%s-%s.sql' % (self.env['db_name'], self.env['ms'])
        run('pg_dump %s > %s/%s --user=%s' % (self.env['db_name'], self.env['rpath'], filename, self.env['db_user']))
        run('gzip %s/%s' % (self.env['rpath'], filename))
        get('%s/%s.gz' % (self.env['rpath'], filename), 'remote.sql.gz')
        run('rm %s/%s.gz' % (self.env['rpath'], filename))
        try:
            local('pg_dump %s > db.%s.sql --user=%s --host=%s' % (self.env['local_db_name'], self.env['ms'], self.env['local_db_user'], self.env['local_db_host']))
            local('dropdb -U %s %s --host=%s' % (self.env['local_db_user'], self.env['local_db_name'], self.env['local_db_host']))
        except:
            pass
        local('createdb -U %s %s --encoding=UNICODE --host=%s' % (self.env['local_db_user'], self.env['local_db_name'], self.env['local_db_host']))
        local('gunzip remote.sql.gz')
        local('psql -U %s %s < remote.sql --host=%s' % (self.env['local_db_user'], self.env['local_db_name'], self.env['local_db_host']))
        local('rm remote.sql')
    
    def update_virtualenv(self):
        result = run(self.env['workon_remote'] + 'pip install -r %s/d/current/requirements.txt -U' % self.env['rpath'])
        if result.failed and not confirm('Virtualenv sync failure! Continue?'):
            abort('Aborting')
        self.reload_remote()

    def install_virtualenv(self):
        result = run(self.env['workon_remote'] + 'pip install -r %s/d/hot/requirements.txt' % self.env['rpath'])
        if result.failed and not confirm('Virtualenv sync failure! Continue?'):
            abort('Aborting')
    