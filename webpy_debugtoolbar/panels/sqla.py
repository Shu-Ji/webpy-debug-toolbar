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
        return self.render('panels/sqlalchemy.html', {'queries': data})

# Panel views

class SqlaHandler:
    def POST(self, type):
        i = web.input()
        statement = i['sql']
        params = i['params']

        # Validate hash
        hash = hashlib.sha1(
            web.config.SECRET_KEY + statement + params).hexdigest()
        if hash != i['hash']:
            raise web.notacceptable()

        # Make sure it is a select statement
        if not statement.lower().strip().startswith('select'):
            raise web.notacceptable()

        params = json.loads(params)

        engine = web.config.engine

        if type == 'explain':
            if engine.driver == 'pysqlite':
                statement = 'EXPLAIN QUERY PLAN %s' % statement
            else:
                statement = 'EXPLAIN %s' % statement
            
        result = engine.execute(statement, params)
        debugtoolbar = web.config.debug_toolbar
        return debugtoolbar.render('panels/sqla_result.html', {
            'result': result.fetchall(),
            'headers': result.keys(),
            'sql': format_sql(statement, params),
            'duration': float(i['duration']),
            'type': type,
        })
