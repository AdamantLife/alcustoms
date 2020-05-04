from alcustoms import sql
from alcustoms.sql.objects import graphdb

from flask import current_app, g


def get_db(connection = None):
    if 'db' not in g:
        if connection == "graph":
            Connection = graphdb.GraphDB
            row_factory = graphdb.node_factory
        else:
            Connection = sql.Database
            row_factory = sql.advancedrow_factory
        g.db = Connection(current_app.config['DATABASE_PATH'])
        g.db.row_factory = row_factory

    return g.db

def close_db(e = None):
    db = g.pop('db',None)

    if db is not None:
        db.close()


def init_app(app):
    app.get_db = get_db
    app.teardown_appcontext(close_db)