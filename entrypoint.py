#!/usr/bin/env python
# encoding: utf-8

from __future__ import unicode_literals
from __future__ import print_function

import os
import sys
import psycopg2

if not sys.platform.startswith('win'):
    import readline

'''
关闭selinux 
sudo setenforce 0
docker pull postgres:9.5
docker pull espushcloud/server:latest
mkdir data log
docker run -v `pwd`/data:/var/lib/postgresql/data --name db -e POSTGRES_PASSWORD=123456 -d postgres:9.5
docker run --link db:db -e POSTGRES_PASSWORD=123456 -i -t espushcloud/server init
docker run -p 10081:10081 -p 8000:8000 --link db:db -e DBCONNSTR=postgresql://postgres:123456@db/template1 -v `pwd`/log:/usr/src/app/log -d espushcloud/server


TODO:
0, db init
1, db struct init
2, log dir
'''


def dbinit(user, pwd, dbname):
    db_admin_user = 'postgres'
    if 'POSTGRES_PASSWORD' not in os.environ:
        print('cannot found ENV: POSTGRES_PASSWORD, using default.')
        db_admin_pwd = '123456'
    else:
        db_admin_pwd = os.environ['POSTGRES_PASSWORD']
    conn = psycopg2.connect(user=db_admin_user, password=db_admin_pwd, dbname='postgres', host='db')
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("create user %s createdb password '%s';" % (user, pwd))
    cursor.close()
    conn.close()
    conn = psycopg2.connect(user=user, password=pwd, dbname='postgres', host='db')
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute('create database %s' % dbname)
    cursor.close()
    conn.close()
    cmd = 'docker run -p 10081:10081 -p 8000:8000 --link db:db -e DBCONNSTR=postgresql://%s:%s@db/%s -v `pwd`/log:/usr/src/app/log -d espushcloud/server' % (user, pwd, dbname)
    print('Database INIT COMPELETE')
    print('PLEASE, run %s' % cmd)


def django_db_init(user, pwd):
    os.system('python manage.py makemigrations webv2')
    os.system('python manage.py makemigrations weixin')
    os.system('python manage.py migrate')
    # os.system('python manage.py createsuperuser')


def server_forever():
    os.system('cd gateway && python router.py &')
    os.system('cd gateway && python svc_espush.py &')
    os.system('python manage.py runserver 0.0.0.0:8000')


def init():
    '''
    1, connect to db, create user, reconn, create db
    2, manage.py makemigrations webv2/weixin/migrate
    3, manage.py createsuperuser ...
    '''
    dbuser = raw_input('Database Username [default: espush]>')
    if not dbuser:
        dbuser = 'espush'
    dbpwd = raw_input('Database Password >')
    if not dbpwd:
        print('EMPTY PASSWORD?')
        sys.exit(1)
    dbname = raw_input('Database Name [default: espush]>')
    if not dbname:
        dbname = 'espush'
    admin_user = raw_input('Administrator Username: [default: admin@espush.cn]>')
    if not admin_user:
        admin_user = 'admin@espush.cn'
    admin_pwd = raw_input('Administrator Password >')
    if not admin_pwd:
        print('EMPTY ADMINISTRATOR PASSWORD?')
        sys.exit(1)
    try:
        dbinit(dbuser, dbpwd, dbname)
    except psycopg2.Error as _:
        print('Database init failed!')
        sys.exit(1)
    dbstr = 'postgresql://%s:%s@db/%s' % (dbuser, dbpwd, dbname)
    print('DB CONNECT STR: %s' % dbstr)
    os.environ['DBCONNSTR'] = dbstr
    django_db_init(admin_user, admin_pwd)


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'init':
        try:
            init()
        except KeyboardInterrupt as _:
            print('Quit')
            sys.exit(1)
    elif len(sys.argv) == 1:
        server_forever()
    elif len(sys.argv) == 2 and sys.argv[1] == 'server':
        server_forever()
    elif len(sys.argv) == 2:
        os.system(' '.join(sys.argv[1:]))
