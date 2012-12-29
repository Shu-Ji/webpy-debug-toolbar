import os

import web
from web.contrib.template import render_jinja

from webpy_debugtoolbar import DebugToolbarExtension


# some settings
PROJ_ROOT = os.path.dirname(__file__)
TEMPLATE_DIR = os.path.join(PROJ_ROOT, 'templates')
render = render_jinja(TEMPLATE_DIR)


urls = (
    '/', 'index',
)
web.config.debug = True
web.config.DEBUG_TB_PANELS = {
    'DEBUG_TB_INTERCEPT_REDIRECTS': True,
    'DEBUG_TB_PANELS': (
        'webpy_debugtoolbar.panels.versions.VersionDebugPanel',
        'webpy_debugtoolbar.panels.profiler.ProfilerDebugPanel',
        'webpy_debugtoolbar.panels.timer.TimerDebugPanel',
        'webpy_debugtoolbar.panels.headers.HeaderDebugPanel',
        'webpy_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
        'webpy_debugtoolbar.panels.logger.LoggingPanel',
    )
}


class index:
    def GET(self):
        import logging
        logging.error('hello world.')
        return render.index()


# add urls and global static file handler
app_wrapper = DebugToolbarExtension.app_wrapper(urls, globals())
web.config.app = app = web.application(*app_wrapper)

# for session panel
web.config.session = web.session.Session(app, web.session.DiskStore('sessions'))
web.config.session.test_session = ['hello', 'foo']

# for logging panel
web.config.proj_root = PROJ_ROOT


if web.config.debug:
    DebugToolbarExtension(app)


if __name__ == "__main__":
    app.run()
