# -*- coding:utf-8 -*-
import logging
import sys
import json
from prestring import NameStore
from dictknife import Accessor
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
        self.accessor = Accessor()

    def resolve_view_path(self, rootdata, d):
        return d["operationId"]

    def resolve_module_name(self, view_path):
        return view_path.rsplit(".", 1)[0]

    def resolve_route_name(self, module_name, pattern):
        k = (module_name, pattern)
        self.route_name_store[k] = module_name
        return self.route_name_store[k]

    def resolve_ref(self, fulldata, d):
        # todo: support quoted "/"
        if "$ref" not in d:
            return d
        path = d["$ref"][len("#/"):].split("/")
        name = path[-1]

        parent = self.accessor.maybe_access_container(fulldata, path)
        if parent is None:
            sys.stderr.write("\t{!r} is not found\n".format(d["$ref"]))
            return d
        return self.resolve_ref(fulldata, parent[name])

    def view_docstring(self, fulldata, d):
        if "parameters" not in d:
            return None
        parameters = [self.resolve_ref(fulldata, pd) for pd in d["parameters"]]
        return json.dumps(parameters, indent=2, ensure_ascii=False).replace("\n", "\n    ")
