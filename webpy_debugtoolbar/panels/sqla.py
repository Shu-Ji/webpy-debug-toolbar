import hashlib
import time
import logging
import json

from sqlalchemy import event
from sqlalchemy.engine import Engine
 
import web

from webpy_debugtoolbar.panels import DebugPanel
from webpy_debugtoolbar.utils import format_fname, format_sql


web.config.debug_toolbar_queries = []

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, 
                        parameters, context, executemany):
    context._query_start_time = time.time()


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, 
                        parameters, context, executemany):
    total = time.time() - context._query_start_time
    web.config.debug_toolbar_queries.append(
        (statement, parameters, total, context))


_ = lambda x: x


def _calling_context(app_path):
    import sys
    frm = sys._getframe(1)
    while frm.f_back is not None:
        name = frm.f_globals.get('__name__')
        if name and (name == app_path or name.startswith(app_path + '.')):
            funcname = frm.f_code.co_name
            return '%s:%s (%s)' % (
                frm.f_code.co_filename,
                frm.f_lineno,
                funcname
            )
        frm = frm.f_back
    return '<unknown>'


class SQLAlchemyDebugPanel(DebugPanel):
    """
    Panel that displays the time a response took in milliseconds.
    """
    name = 'SQLAlchemy'

    @property
    def has_content(self):
        return bool(web.config.debug_toolbar_queries)

    def process_request(self):
        pass

    def process_response(self, response):
        pass

    def nav_title(self):
        return _('SQLAlchemy')

    def nav_subtitle(self):
        count = len(web.config.debug_toolbar_queries)
        return "%d %s" % (count, "query" if count == 1 else "queries")

    def title(self):
        return _('SQLAlchemy queries')

    def url(self):
        return ''

    def content(self):
        data = []
        for query in web.config.debug_toolbar_queries:
            statement, parameters, duration, context = query
            is_select = statement.strip().lower().startswith('select')
            _params = ''
            try:
                _params = json.dumps(parameters)
            except TypeError:
                pass # object not JSON serializable

            web.config.setdefault('SECRET_KEY', 'webpy_debugtoolbar_secret')
            hash = hashlib.sha1(
                web.config.SECRET_KEY +
                statement + _params).hexdigest()

            data.append({
                'duration': duration,
                'sql': format_sql(statement, parameters),
                'raw_sql': statement,
                'hash': hash,
                'params': _params,
                'is_select': is_select,
            })
        web.config.debug_toolbar_queries = []
        return self.render('panels/sqlalchemy.html', { 'queries': data})

# Panel views

#@module.route('/sqlalchemy/sql_select', methods=['GET', 'POST'])
def sql_select():
    statement = request.args['sql']
    params = request.args['params']

    # Validate hash
    hash = hashlib.sha1(
        current_app.config['SECRET_KEY'] + statement + params).hexdigest()
    if hash != request.args['hash']:
        return abort(406)

    # Make sure it is a select statement
    if not statement.lower().strip().startswith('select'):
        return abort(406)

    params = json.loads(params)

    engine = SQLAlchemy().get_engine(current_app)

    result = engine.execute(statement, params)
    return g.debug_toolbar.render('panels/sqlalchemy_select.html', {
        'result': result.fetchall(),
        'headers': result.keys(),
        'sql': format_sql(statement, params),
        'duration': float(request.args['duration']),
    })

#@module.route('/sqlalchemy/sql_explain', methods=['GET', 'POST'])
def sql_explain():
    statement = request.args['sql']
    params = request.args['params']

    # Validate hash
    hash = hashlib.sha1(
        current_app.config['SECRET_KEY'] + statement + params).hexdigest()
    if hash != request.args['hash']:
        return abort(406)

    # Make sure it is a select statement
    if not statement.lower().strip().startswith('select'):
        return abort(406)

    params = json.loads(params)

    engine = SQLAlchemy().get_engine(current_app)

    if engine.driver == 'pysqlite':
        query = 'EXPLAIN QUERY PLAN %s' % statement
    else:
        query = 'EXPLAIN %s' % statement

    result = engine.execute(query, params)
    return g.debug_toolbar.render('panels/sqlalchemy_explain.html', {
        'result': result.fetchall(),
        'headers': result.keys(),
        'sql': format_sql(statement, params),
        'duration': float(request.args['duration']),
    })
