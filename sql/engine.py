from alcustoms import sql

from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sql.Database(current_app.config['DATABASE_PATH'])
        g.db.row_factory = sql.advancedrow_factory

    return g.db

def close_db(e = None):
    db = g.pop('db',None)

    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)