# -*- coding:utf-8 -*-
from collections import OrderedDict
from redbaron import RedBaron, nodes, base_nodes
import logging


logger = logging.getLogger(__name__)


# TODO: issued upstream (this is work-around monkey patch)
def patched__get_separator_indentation(self):
    default_indent = "    "
    if self.parent is not None:
        default_indent = self.parent.indentation + default_indent
    return self.node_list.filtered()[
        0].indentation if self.node_list.filtered() else default_indent
base_nodes.LineProxyList._get_separator_indentation = patched__get_separator_indentation


class FunctionDefModifier(object):
    additionals = []

    def on_additional_create(self, name, t0):
        logger.debug("create def: name=%s", name)

    def on_additional_update(self, name, node, t0):
        logger.debug("update def: name=%s", name)

    def on_create(self, name, node):
        logger.debug("create def: name=%s", name)
        return node

    def on_update(self, name, node, original):
        logger.debug("update def: name=%s", name)
        return original

    def modify(self, base, additional):
        t0 = RedBaron(base)
        t1 = RedBaron(additional)
        d = OrderedDict()
        used = set()
        for node in t0.find_all("def", recursive=False):
            used.add(node.name)
            d[node.name] = node

        for node in t1.find_all("def", recursive=False):
            if node.name in used:
                original = d[node.name]
                self.on_update(node.name, node, original)
            else:
                newnode = self.on_create(node.name, node)
                if newnode is not None:
                    t0.append(newnode)
                d[node.name] = newnode

        for name in self.additionals:
            if name not in d:
                self.on_additional_create(name, t0)
            else:
                self.on_additional_update(name, d[name], t0)
        return t0


class ViewsModifier(FunctionDefModifier):
    def __init__(self):
        self.docstring = DocstringUpdateHandler()
        self.decorator = ViewConfigDecoratorUpdateHandler()

    def on_update(self, name, node, original):
        super().on_update(name, node, original)
        self.docstring.on_update(name, node, original)
        self.decorator.on_update(name, node, original)
        return original


class RoutesModifier(FunctionDefModifier):
    additionals = ["includeme"]

    def on_additional_create(self, name, t0):
        assert name == "includeme"
        super().on_additional_create(name, t0)
        """"""
        includeme = """
def includeme(config):
    config.include(includeme_swagger_router)
"""
        t0.node_list.append(RedBaron(includeme))

    def on_additional_update(self, name, node, t0):
        super().on_additional_update(name, node, t0)
        assert name == "includeme"
        """"""
        includeme = """config.include(includeme_swagger_router)"""
        for sentence in node.value:
            if str(sentence) == includeme:
                return
        node.insert(0, RedBaron(includeme))

    def on_update(self, name, node, original):
        if name == "includeme_swagger_router":
            original.value = node.value


class DocstringUpdateHandler(object):
    def on_update(self, name, node, original):
        if not self.has_docstring(node):
            return
        if not self.has_docstring(original):
            original.insert(0, node[0])
        else:
            original[0].replace(node[0])

    def has_docstring(self, node):
        return isinstance(node[0], nodes.StringNode)


class ViewConfigDecoratorUpdateHandler(object):
    # override
    def on_update(self, name, node, original):
        if not self.has_decorator(node):
            return

        view_config = find_decorator(node, "view_config")
        if view_config is None:
            return
        if not self.has_decorator(original):
            original.decorators.append(view_config)
        else:
            original_view_config = find_decorator(original, "view_config")
            merge_decorator(original_view_config, view_config)

    def has_decorator(self, node):
        return bool(node.decorators)


def find_decorator(node, name):
    for deco in node.decorators:
        if str(deco.dotted_name) == name:
            return deco
    return None


def merge_decorator(deco_node0, deco_node1):
    d = OrderedDict()
    for arg in deco_node0.call.value:
        name, value = str(arg).split("=", 1)
        d[name] = value
    for arg in deco_node1.call.value:
        name, value = str(arg).split("=", 1)
        d[name] = value
    call = deco_node0.call
    # clear
    for i in range(len(call.value)):
        del call.value[0]
    for name, value in d.items():
        call.append("=".join((name, value)))
    return deco_node0
