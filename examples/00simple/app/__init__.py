from wsgiref.simple_server import make_server
from pyramid.config import Configurator
import os.path


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    settings = {"pyramid.reload_all": True, "here": here}
    config = Configurator(settings=settings)
    config.include(".routes")
    app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 8080, app)
    server.serve_forever()

if __name__ == "__main__":
    main()
