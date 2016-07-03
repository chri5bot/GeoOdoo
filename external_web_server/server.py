import os
import views
from werkzeug.wrappers import Request, Response
from werkzeug.wsgi import ClosingIterator
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from jinja2 import Environment, FileSystemLoader

URLS = Map([
    Rule('/activate_account', endpoint='activate_account'),
    Rule('/tests', endpoint='tests')
])

class ExternalServer(object):

    def __init__(self):
        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_path),autoescape=True)
        self.url_map = URLS

    def render_template(self, template_name, **context):
        t = self.jinja_env.get_template(template_name)
        return Response(t.render(context), mimetype='text/html')

    def dispatch(self, environ, start_response):
        request = Request(environ)
        adapter = self.url_map.bind_to_environ(environ)
        try:
            endpoint, values = adapter.match()
            handler = getattr(views, endpoint)
            method = getattr(handler, "response")
            response = method(app, request, **values)
        except NotFound, e:
            response = self.render_template('404.html')
            response.status_code = 404
        except HTTPException, e:
            response = e
        return ClosingIterator(response(environ, start_response))

    def __call__(self, environ, start_response):
        return self.dispatch(environ, start_response)

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    app = ExternalServer()
    run_simple('0.0.0.0', 8080, app, use_debugger=True, use_reloader=True)