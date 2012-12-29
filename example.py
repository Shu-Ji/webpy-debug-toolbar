import os

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

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
        'webpy_debugtoolbar.panels.sqla.SQLAlchemyDebugPanel',
    )
}



# add urls and global static file handler for webpy debug toolbar
app_wrapper = DebugToolbarExtension.app_wrapper(urls, globals())
web.config.app = app = web.application(*app_wrapper)
if web.config.debug:
    DebugToolbarExtension(app)
# for session panel
web.config.session = web.session.Session(app, web.session.DiskStore('session'))
web.config.session.test_session = ['hello', 'foo']
# for logging panel
web.config.proj_root = PROJ_ROOT
# web.config.SECRET_KEY = '@;TestSqlalchemyPanel!'
# default is: SECRET_KEY = 'webpy_debugtoolbar_secret'



# SQLAlchemy settings
engine = create_engine(
    'sqlite:///tutorial.db',
    encoding='utf8',
    echo=False,
)
# db means the session of sqlalchemy.(To be different from session of web.py)
db = scoped_session(sessionmaker(bind=engine))
# some models
Base= declarative_base()
class Account(Base):
    __tablename__ = 'account'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
Base.metadata.create_all(engine)



class index:
    def GET(self):
        # test logger
        import logging
        logging.error('hello world.')

        # test SQLAlchemy
        count = db.query(Account.uid).count()
        name='webpy name %s' % (count + 1)
        db.add(Account(name=name))
        db.commit()
     
        return render.index(locals())


if __name__ == "__main__":
    app.run()
