# -*- coding:utf-8 -*-
import logging
import sys
import json
from prestring import NameStore, Module
from dictknife import Accessor
from collections import defaultdict
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

    def resolve_route_name(self, module_name, pattern, route_name=None):
        if route_name is not None:
            return route_name
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

    rename_dict = {
        "path": "request.matchdict:",
        "query": "request.GET:",
        "formData": "request.POST:",
        "body": "request.json_body:"
    }

    def view_docstring(self, fulldata, d, rename_dict=rename_dict):
        if "parameters" not in d:
            return None
        parameters = defaultdict(list)
        for p in d["parameters"]:
            p = self.resolve_ref(fulldata, p)
            parameters[p["in"]].append(p)

        # "query", "header", "path", "formData" or "body"
        m = Module()
        body = parameters.pop("body", None)
        for name, vs in parameters.items():
            pyramid_name = rename_dict.get(name) or name
            m.stmt(pyramid_name)
            m.stmt("")
            with m.scope():
                for v in vs:
                    name = v.get("name", "")
                    description = v.get("description", "-")
                    if description:
                        description = "  {}".format(description)

                    extra = v.copy()
                    extra.pop("in", None)
                    extra.pop("name", None)
                    extra.pop("description", None)
                    if extra:
                        extra_string = "  `{}`".format(json.dumps(extra))
                    else:
                        extra_string = ""
                    m.stmt("* {name!r}{description}{extra}".format(name=name, description=description, extra=extra_string))

        if body:
            m.stmt("")
            m.stmt(rename_dict["body"])
            m.stmt("\n```")
            with m.scope():
                schema = self.resolve_ref(fulldata, body[0]["schema"])
                json_str = json.dumps(schema, ensure_ascii=False, indent=2)
                for line in json_str.split("\n"):
                    m.stmt(line)
            m.stmt("```")
        return str(m)
