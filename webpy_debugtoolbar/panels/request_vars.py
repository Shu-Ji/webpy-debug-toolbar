import web

from webpy_debugtoolbar.panels import DebugPanel

_ = lambda x: x

class RequestVarsDebugPanel(DebugPanel):
    """
    A panel to display request variables (POST/GET, session, cookies).
    """
    name = 'RequestVars'
    has_content = True

    def nav_title(self):
        return _('Request Vars')

    def title(self):
        return _('Request Vars')

    def url(self):
        return ''

    def process_request(self):
        self.view_func = None
        self.view_args = []
        self.view_kwargs = {}

    def content(self):
        session = web.config.session
        i = web.input()
        cookies = web.cookies()
        context = self.context.copy()
        context.update({
            'get': [(k, i[k]) for k in i.keys()],
            'cookies': [(k, cookies.get(k)) for k in cookies],
            'session': [(k, v) for k,v in session.items()],
        })

        return self.render('panels/request_vars.html', context)

