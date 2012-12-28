import web
import os
from web.contrib.template import render_jinja

APP_ROOT = os.path.dirname(__file__)
TEMPLATE_DIR = os.path.join(APP_ROOT, 'templates')
render = render_jinja(TEMPLATE_DIR)

from webpy_debugtoolbar import DebugToolbarExtension
from webpy_debugtoolbar import _debug_toolbar_path 

urls = (
    '/', 'index',
    '/_debug_toolbar/(static/.*?)', 'DebugToolbarStaticFileHandler',
)


class DebugToolbarStaticFileHandler: 
    def GET(self, path):
        import mimetypes
        import datetime
        import stat
        import hashlib
        abspath = os.path.join(_debug_toolbar_path, path)
        stat_result = os.stat(abspath)
        modified = datetime.datetime.fromtimestamp(stat_result[stat.ST_MTIME])
        web.header("Last-Modified", modified)

        mime_type, encoding = mimetypes.guess_type(abspath)
        if mime_type:
            web.header("Content-Type", mime_type)

        cache_time = 86400 * 365 * 10
        web.header("Expires", datetime.datetime.now() + \
                   datetime.timedelta(seconds=cache_time))
        web.header("Cache-Control", "max-age=%s" % cache_time)

        ims_value = web.ctx.env.get("HTTP_IF_MODIFIED_SINCE")
        if ims_value is not None:
            since = datetime.datetime.strptime(ims_value, '%Y-%m-%d %H:%M:%S')
            if since >= modified:
                raise web.notmodified()

        with open(abspath, "rb") as f:
            data = f.read()
            hasher = hashlib.sha1()
            hasher.update(data)
            web.header("Etag", '"%s"' % hasher.hexdigest())
            return data


web.config.debug = True
web.config.DEBUG_TB_PANELS = {
    'DEBUG_TB_INTERCEPT_REDIRECTS': True,
    'DEBUG_TB_PANELS': (
        'webpy_debugtoolbar.panels.versions.VersionDebugPanel',
        'webpy_debugtoolbar.panels.profiler.ProfilerDebugPanel',
        'webpy_debugtoolbar.panels.timer.TimerDebugPanel',
        'webpy_debugtoolbar.panels.headers.HeaderDebugPanel',
        'webpy_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
        #'webpy_debugtoolbar.panels.template.TemplateDebugPanel',
    )
}


class index:
    def GET(self):
        return render.index()


web.config.app = app = web.application(urls, globals())
web.config.session = web.session.Session(app, web.session.DiskStore('sessions'))
web.config.session.test_session = ['hello', 'foo']
toolbar = DebugToolbarExtension(app)


if __name__ == "__main__":
    app.run()
