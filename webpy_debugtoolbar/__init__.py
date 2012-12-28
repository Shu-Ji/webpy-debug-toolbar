import os
import web

from jinja2 import Environment, PackageLoader
from werkzeug.exceptions import HTTPException
from werkzeug.urls import url_quote_plus

from webpy_debugtoolbar.toolbar import DebugToolbar

_debug_toolbar_path = os.path.dirname(__file__)

def replace_insensitive(string, target, replacement):
    """Similar to string.replace() but is case insensitive
    Code borrowed from: http://forums.devshed.com/python-programming-11/case-insensitive-string-replace-490921.html
    """
    no_case = string.lower()
    index = no_case.rfind(target.lower())
    if index >= 0:
        return string[:index] + replacement + string[index + len(target):]
    else: # no results so return the original string
        return string


def _printable(value):
    if isinstance(value, unicode):
        return value.encode('unicode_escape')
    elif isinstance(value, str):
        return value.encode('string_escape')
    else:
        return repr(value)


class DebugToolbarExtension(object):
    _static_dir = os.path.realpath(
        os.path.join(os.path.dirname(__file__), 'static'))

    _redirect_codes = [301, 302, 303, 304]

    def __init__(self, app):
        self.app = app
        self.debug_toolbars = None
        self.hosts = ()
        loaded = web.config.get('DEBUG_TB_PANELS_LOADED')
        if loaded is None:
            web.config.DEBUG_TB_PANELS_LOADED = True
            DebugToolbar.load_panels()

        def my_processor(handler): 
            self.process_request()
            return self.process_response(handler())

        self.app.add_processor(my_processor)

        # Configure jinja for the internal templates and add url rules
        # for static data
        self.jinja_env = Environment(
            autoescape=True,
            extensions=['jinja2.ext.i18n', 'jinja2.ext.with_'],
            loader=PackageLoader(__name__, 'templates'))
        self.jinja_env.filters['urlencode'] = url_quote_plus
        self.jinja_env.filters['printable'] = _printable

    def _show_toolbar(self):
        """Return a boolean to indicate if we need to show the toolbar."""
        if web.ctx.path.startswith('/_debug_toolbar/'):
            return False

        if self.hosts and web.ctx.env.get('REMOTE_ADDR') not in self.hosts:
            return False

        return True

    def send_static_file(self, filename):
        """Send a static file from the webpy-debugtoolbar static directory."""
        return send_from_directory(self._static_dir, filename)

    def process_request(self):
        web.config.debug_toolbar = self

        if not self._show_toolbar():
            return

        self.debug_toolbars = DebugToolbar(self.jinja_env)
        for panel in self.debug_toolbars.panels:
            panel.process_request()

    def process_response(self, content):
        # If the http response code is 200 then we process to add the
        # toolbar to the returned html response.
        for panel in self.debug_toolbars.panels:
            panel.process_response(content)

        toolbar_html = self.debug_toolbars.render_toolbar()

        content = replace_insensitive(
            content, '</body>', toolbar_html + '</body>')
        web.header('Content-Length', len(content))

        return content

    def teardown_request(self, exc):
        self.debug_toolbars.pop(request._get_current_object(), None)

    def render(self, template_name, context):
        template = self.jinja_env.get_template(template_name)
        return template.render(**context)
