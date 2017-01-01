# -*- coding:utf-8 -*-
import sys
import logging
from collections import defaultdict
from collections import OrderedDict
from prestring import NameStore
from dictknife import loading
from prestring.python import Module

logger = logging.getLogger(__name__)


class RouteNameStore(NameStore):
    def new_name(self, name, i):
        if i == 0:
            return name
        else:
            return "{}{}".format(name, i)


class Resolver(object):
    def __init__(self):
        self.route_name_store = RouteNameStore()

    def resolve_view_path(self, rootdata, d):
        return d["operationId"]

    def resolve_module_name(self, view_path):
        return view_path.rsplit(".", 1)[0]

    def resolve_route_name(self, module_name, pattern):
        k = (module_name, pattern)
        self.route_name_store[k] = module_name
        return self.route_name_store[k]


class Context(object):
    def __init__(self):
        m = self.m = Module()
        self.routes = {}
        with m.def_("includeme", "config"):
            self.fm = m.submodule()

    def add_view_setup(self, pattern, route, sym, method="GET", renderer=None):
        # normalize
        route = route.replace(".", "_")  # xxx
        method = method.upper()

        if route not in self.routes:
            self.add_route(route, pattern)
            self.routes[route] = OrderedDict()

        k = (route, method)
        if k not in self.routes[route]:  # xxx
            self.add_view(sym, route, method)

    def add_route(self, route, pattern):
        self.fm.stmt('config.add_route({!r}, {!r})'.format(route, pattern))

    def add_view(self, sym, route, method):
        self.fm.stmt('config.add_view({!r}, route_name={!r}, request_method={!r})'.format(sym, route, method))


class Driver(object):
    def __init__(self):
        self.resolver = Resolver()

    def run(self, src, dst):
        data = self.load(src)
        result = self.transform(data)
        self.dump(result, dst)

    def load(self, src):
        loading.setup()
        return loading.load(src)

    def dump(self, md, dst):
        for name, ctx in md.items():
            print(name, file=dst)
            print(ctx.m, file=dst)
            print("", file=dst)

    def transform(self, data):
        md = defaultdict(Context)
        for pattern, d in (data.get("paths") or {}).items():
            for method, d in d.items():
                try:
                    view_path = self.resolver.resolve_view_path(data, d)
                except KeyError:
                    sys.stderr.write("route is not resolved from {!r}\n".format(["paths", pattern, method]))
                    continue
                module_name = self.resolver.resolve_module_name(view_path)
                route_name = self.resolver.resolve_route_name(module_name, pattern)
                md[module_name].add_view_setup(pattern, route_name, view_path, method=method)

        return md
