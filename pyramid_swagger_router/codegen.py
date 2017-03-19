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

    def build_view_setting(self, pattern, route, method, renderer="json", here=None):
        kwargs = OrderedDict()
        kwargs["route_name"] = route
        kwargs["request_method"] = method
        kwargs["renderer"] = renderer
        return kwargs


class _RouteContext(object):
    def __init__(self, parent):
        self.scanned = set()
        self.parent = parent
        m = self.m = Module()
        with m.def_("includeme_swagger_router", "config"):
            self.fm = m.submodule()
            self.scanm = m.submodule()
        with m.def_("includeme", "config"):
            m.stmt("config.include(includeme_swagger_router)")

    def add_route(self, route, pattern, d):
        self.fm.stmt('config.add_route({!r}, {!r})'.format(route, pattern))

    def add_view(self, pattern, sym, route, method, d):
        view_setting = self.parent.build_view_setting(pattern, route, method, here=self)
        self.fm.stmt('config.add_view({!r}, {})'.format(sym, LazyKeywordsRepr(view_setting)))

    def add_scan(self, view_module):
        if self.parent.options.use_view_config:
            self.scanm.stmt("config.scan('.{}')".format(view_module.split(".")[-1]))


class _ViewContext(object):
    def __init__(self, parent):
        self.parent = parent
        self.m = Module(import_unique=True)
        self.im = self.m.submodule()
        self.m.sep()
        # todo: scan module file

    def add_view(self, pattern, sym, route, method, d, docstring=None):
        name = sym.rsplit(".", 1)[-1]
        m = self.m
        self.from_("pyramid.view", "view_config")

        view_setting = self.parent.build_view_setting(pattern, route, method, here=self)
        m.stmt(LazyFormat("@view_config({})", LazyKeywordsRepr(view_setting)))
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
    def __init__(self, output, context_factory=Context):
        self.output = output
        self.contexts = {}
        self.routes = {}
        self.views = {}
        self.context_factory = context_factory

    def get_context(self, module_name):
        if module_name in self.contexts:
            return self.contexts[module_name]
        context = self.contexts[module_name] = self.context_factory()
        view_path = "{}.py".format(module_name.replace(".", "/"))

        if len(module_name.split(".")) <= 2:
            route_path = os.path.join(os.path.dirname(view_path), "routes.py")
        else:
            route_path = os.path.join(os.path.dirname(view_path), "__init__.py")

        if route_path in self.routes:
            context.route = self.routes[route_path]
        else:
            route_file = self.output.new_file(route_path, m=context.route.m)
            self.output.files[route_file.name] = route_file
            self.routes[route_path] = context.route
        context.route.add_scan(module_name)
        view_file = self.output.new_file(view_path, m=context.view.m)
        self.views[view_file.name] = view_file
        self.output.files[view_file.name] = view_file
        return context

    def _get_or_create_route_file(self, path, context):
        if path in self.output.files:
            f = self.output.files[path]
            return f
        else:
            return self.output.new_file(path, m=context.route.m)


class Codegen(object):
    def __init__(self, resolver, context_factory=Context):
        self.resolver = resolver
        self.view_func_modifier = ViewsModifier()
        self.route_func_modifier = RoutesModifier()
        self.context_factory = context_factory

    def add_routing(self, store, fulldata):
        base_path = fulldata.get("basePath")
        for pattern, d in (fulldata.get("paths") or {}).items():
            if base_path is not None:
                pattern = "{}/{}".format(base_path.rstrip("/"), pattern.lstrip("/"))
            route_name = d.get("x-pyramid-route-name", None)
            base_paramerters = d.get("parameters")
            for method, d in d.items():
                if method == "parameters":
                    continue
                if method.startswith("x-"):
                    continue

                if base_paramerters is not None:
                    d["parameters"] = base_paramerters + (d.get("parameters") or [])

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
                        ctx.view.add_view(pattern, view_path, route, method, d, docstring)
                    else:
                        ctx.route.add_view(pattern, view_path, route, method, d)

    def merge_routing(self, store):
        fs = store.output.files
        for name, f in list(fs.items()):
            if name in store.views:
                path = os.path.join(store.output.dirname, name)
                if os.path.exists(path):
                    logger.info("merge file: %s", path)
                    with open(path) as rf:
                        t = self.view_func_modifier.modify(rf.read(), str(f.m))
                        fs[name] = File(name=name, m=t.dumps())
            elif name in store.routes:
                path = os.path.join(store.output.dirname, name)
                if os.path.exists(path):
                    logger.info("merge file: %s", path)
                    with open(path) as rf:
                        t = self.route_func_modifier.modify(rf.read(), str(f.m))
                        fs[name] = File(name=name, m=t.dumps())

    def codegen(self, data, output):
        store = ContextStore(output, context_factory=self.context_factory)
        self.add_routing(store, data)
        self.merge_routing(store)
        return store.output
