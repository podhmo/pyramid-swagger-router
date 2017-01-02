# -*- coding:utf-8 -*-
import sys
import logging
import os.path
from collections import OrderedDict
from prestring.python import Module
from prestring import LazyKeywordsRepr, LazyFormat
from prestring.output import File
from .asthandler import ViewsModifier, RoutesModifier

logger = logging.getLogger(__name__)


class OptionHandler(object):
    def __init__(self, options):
        self.options = options

    @property
    def use_view_config(self):
        return self.options.get("use_view_config", False)


class Context(object):
    def __init__(self, options={"use_view_config": True}):
        self.options = OptionHandler(options)
        self.route = _RouteContext(parent=self)
        self.view = _ViewContext(parent=self)
        self.used = {}


class _RouteContext(object):
    def __init__(self, parent):
        self.parent = parent
        m = self.m = Module()
        with m.def_("includeme_swagger_router", "config"):
            self.fm = m.submodule()
            if parent.options.use_view_config:
                m.stmt("config.scan('.views')")

        with m.def_("includeme", "config"):
            m.stmt("config.include(includeme_swagger_router)")

    def add_route(self, route, pattern, d):
        self.fm.stmt('config.add_route({!r}, {!r})'.format(route, pattern))

    def add_view(self, sym, route, method, d):
        self.fm.stmt('config.add_view({!r}, route_name={!r}, request_method={!r}, renderer="json")'.format(sym, route, method))


class _ViewContext(object):
    def __init__(self, parent):
        self.parent = parent
        self.m = Module(import_unique=True)
        self.im = self.m.submodule()
        self.m.sep()
        # todo: scan module file

    def add_view(self, sym, route, method, d, docstring=None):
        name = sym.rsplit(".", 1)[-1]
        m = self.m
        self.from_("pyramid.view", "view_config")

        m.stmt(LazyFormat("@view_config({})", LazyKeywordsRepr(dict(route_name=route, request_method=method, renderer="json"))))
        with m.def_(name, "context", "request"):
            m.stmt('"""')
            if "summary" in d:
                m.stmt(d["summary"])
            if docstring:
                m.stmt("")
                for line in docstring.split("\n"):
                    m.stmt(line)
            m.stmt('"""')
            m.return_("{}")

    def from_(self, module, name):
        logger.debug("      import: module=%s, name=%s", module, name)
        self.im.from_(module, name)

    def import_(self, module):
        logger.debug("      import: module=%s", module)
        self.im.import_(module)


class ContextStore(object):
    def __init__(self, output):
        self.output = output
        self.contexts = {}

    def get_context(self, module_name):
        if module_name in self.contexts:
            return self.contexts[module_name]
        context = self.contexts[module_name] = Context()
        dirname = module_name.replace(".", "/")
        route_file = self.output.new_file(os.path.join(dirname, "__init__.py"), m=context.route.m)
        view_file = self.output.new_file(os.path.join(dirname, "views.py"), m=context.view.m)
        self.output.files[route_file.name] = route_file
        self.output.files[view_file.name] = view_file
        return context


class Codegen(object):
    def __init__(self, resolver):
        self.resolver = resolver
        self.view_func_modifier = ViewsModifier()
        self.route_func_modifier = RoutesModifier()

    def add_routing(self, store, fulldata):
        base_path = fulldata.get("basePath")
        for pattern, d in (fulldata.get("paths") or {}).items():
            if base_path is not None:
                pattern = "{}/{}".format(base_path.rstrip("/"), pattern.lstrip("/"))
            route_name = d.get("x-pyramid-route-name", None)
            for method, d in d.items():
                if method.startswith("x-"):
                    continue
                try:
                    view_path = self.resolver.resolve_view_path(fulldata, d)
                except KeyError:
                    sys.stderr.write("route is not resolved from {!r}\n".format(["paths", pattern, method]))
                    continue
                module_name = self.resolver.resolve_module_name(view_path)
                route_name = self.resolver.resolve_route_name(module_name, pattern, route_name=route_name)
                ctx = store.get_context(module_name)

                # normalize
                route = route_name.replace(".", "_")  # xxx
                method = method.upper()

                if route not in ctx.used:
                    ctx.route.add_route(route, pattern, d)
                    ctx.used[route] = OrderedDict()

                k = (route, method)
                if k not in ctx.used[route]:  # xxx
                    if ctx.options.use_view_config:
                        docstring = self.resolver.view_docstring(fulldata, d)
                        ctx.view.add_view(view_path, route, method, d, docstring)
                    else:
                        ctx.route.add_view(view_path, route, method, d)

    def merge_routing(self, store):
        fs = store.output.files
        for name, f in list(fs.items()):
            if name.endswith("views.py"):
                if os.path.exists(name):
                    logger.info("merge file: %s", name)
                    with open(name) as rf:
                        t = self.view_func_modifier.modify(rf.read(), str(f.m))
                        fs[name] = File(name=name, m=t.dumps())
            elif name.endswith("__init__.py"):
                if os.path.exists(name):
                    logger.info("merge file: %s", name)
                    with open(name) as rf:
                        t = self.route_func_modifier.modify(rf.read(), str(f.m))
                        fs[name] = File(name=name, m=t.dumps())

    def codegen(self, data, output):
        store = ContextStore(output)
        self.add_routing(store, data)
        self.merge_routing(store)
        return store.output
