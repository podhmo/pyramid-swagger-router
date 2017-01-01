# -*- coding:utf-8 -*-
import logging
from dictknife import loading
from .codegen import Codegen
from .resolver import Resolver
logger = logging.getLogger(__name__)


class Driver(object):
    def run(self, src, dst):
        data = self.load(src)
        result = self.transform(data)
        self.dump(result, dst)

    def load(self, src):
        loading.setup()
        return loading.load(src)

    def dump(self, output, dst):
        output.output()

    def transform(self, data):
        resolver = Resolver()
        return Codegen(resolver).codegen(data)
