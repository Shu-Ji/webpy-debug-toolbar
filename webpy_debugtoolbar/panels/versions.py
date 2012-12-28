from web import __version__ as webpy_version
from webpy_debugtoolbar.panels import DebugPanel

_ = lambda x: x

class VersionDebugPanel(DebugPanel):
    """
    Panel that displays the webpy version.
    """
    name = 'Version'
    has_content = False

    def nav_title(self):
        return _('Versions')

    def nav_subtitle(self):
        return 'Web.py %s' % webpy_version

    def url(self):
        return ''

    def title(self):
        return _('Versions')

    def content(self):
        return None


