# -*- coding:utf-8 -*-
import logging
from dictknife import loading
from prestring.output import SeparatedOutput
from .codegen import Codegen
from .resolver import Resolver
logger = logging.getLogger(__name__)


class Driver(object):
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
        resolver = Resolver()
        output = SeparatedOutput(dst, prefix="")
        return Codegen(resolver).codegen(data, output)
