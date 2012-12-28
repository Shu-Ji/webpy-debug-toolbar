import urllib
import web


class DebugToolbar(object):

    # default config settings
    config = {
        'DEBUG_TB_INTERCEPT_REDIRECTS': True,
        'DEBUG_TB_PANELS': (
            'webpy_debugtoolbar.panels.versions.VersionDebugPanel',
            'webpy_debugtoolbar.panels.profiler.ProfilerDebugPanel',
            'webpy_debugtoolbar.panels.timer.TimerDebugPanel',
            'webpy_debugtoolbar.panels.headers.HeaderDebugPanel',
            'webpy_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
            'webpy_debugtoolbar.panels.template.TemplateDebugPanel',
            'webpy_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel',
            'webpy_debugtoolbar.panels.logger.LoggingPanel',
        )
    }
    panel_classes = []
    def __init__(self, jinja_env):
        self.jinja_env = jinja_env
        self.panels = []
        self.template_context = {'static': '/_debug_toolbar/static/'}
        self.create_panels()

    @classmethod
    def load_panels(cls):
        cls.config.update(web.config.DEBUG_TB_PANELS)
        web.config.DEBUG_TB_PANELS = cls.config

        for panel_path in cls.config['DEBUG_TB_PANELS']:
            dot = panel_path.rindex('.')
            panel_module, panel_classname = panel_path[:dot], panel_path[dot+1:]

            try:
                mod = __import__(panel_module, {}, {}, [''])
            except ImportError, e:
                print 'Disabled %s due to ImportError: %s' % (panel_classname, e)
                continue
            panel_class = getattr(mod, panel_classname)
            cls.panel_classes.append(panel_class)

    def create_panels(self):
        """
        Populate debug panels
        """
        activated = web.cookies().get('fldt_active', '')
        activated = urllib.unquote(activated).split(';')

        for panel_class in self.panel_classes:
            panel_instance = panel_class(
                context=self.template_context,
                jinja_env=self.jinja_env)

            if panel_instance.dom_id() in activated:
                panel_instance.is_active = True
            self.panels.append(panel_instance)

    def render_toolbar(self):
        context = self.template_context.copy()
        context.update({'panels': self.panels})

        template = self.jinja_env.get_template('base.html')
        return template.render(**context)


