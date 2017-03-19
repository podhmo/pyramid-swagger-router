# -*- coding:utf-8 -*-
import logging
from dictknife import loading
from prestring.output import SeparatedOutput
from .codegen import Codegen
from .resolver import Resolver
logger = logging.getLogger(__name__)


class Driver(object):
    codegen_factory = Codegen
    output_factory = SeparatedOutput
    resolver_factory = Resolver

    def run(self, src, dst):
        data = self.load(src)
        result = self.transform(data, dst)
        self.dump(result)

    def load(self, src):
        loading.setup()
        return loading.load(src)

    def dump(self, output):
        output.output()

    def transform(self, data, dst):
        resolver = self.resolver_factory()
        output = self.output_factory(dst, prefix="")
        return self.codegen_factory(resolver).codegen(data, output)
