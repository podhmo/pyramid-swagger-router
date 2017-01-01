import unittest


class RoutesModifierTests(unittest.TestCase):
    def _makeOne(self):
        from pyramid_swagger_router.asthandler import RoutesModifier
        return RoutesModifier()

    def test_update_includeme(self):
        base = """\
def includeme(config):
    pass
"""
        additional = """\
def includeme_swagger_router(config):
    config.add_route('hello', '/hello')
    config.scan('.views')
"""
        target = self._makeOne()
        result = target.modify(base, additional).dumps()
        expected = """\
def includeme(config):
    config.include(includeme_swagger_router)
    pass
def includeme_swagger_router(config):
    config.add_route('hello', '/hello')
    config.scan('.views')
"""
        self.assertEqual(expected.rstrip(), result.rstrip())

    def test_update_includeme2(self):
        base = """\
def includeme(config):
    config.include(includeme_another)
"""
        additional = """\
def includeme_swagger_router(config):
    config.add_route('hello', '/hello')
    config.scan('.views')
"""
        target = self._makeOne()
        result = target.modify(base, additional).dumps()
        expected = """\
def includeme(config):
    config.include(includeme_swagger_router)
    config.include(includeme_another)
def includeme_swagger_router(config):
    config.add_route('hello', '/hello')
    config.scan('.views')
"""
        self.assertEqual(expected.rstrip(), result.rstrip())

    def test_update_includeme3(self):
        base = """\
def includeme(config):
    config.include(includeme_swagger_router)
"""
        additional = """\
def includeme_swagger_router(config):
    config.add_route('hello', '/hello')
    config.scan('.views')
"""
        target = self._makeOne()
        result = target.modify(base, additional).dumps()
        expected = """\
def includeme(config):
    config.include(includeme_swagger_router)
def includeme_swagger_router(config):
    config.add_route('hello', '/hello')
    config.scan('.views')
"""
        self.assertEqual(expected.rstrip(), result.rstrip())


class ViewsModifierTests(unittest.TestCase):
    def _makeOne(self):
        from pyramid_swagger_router.asthandler import ViewsModifier
        return ViewsModifier()

    def test_add_docstring(self):
        base = ""
        additional = """\
def foo(x):
    '''new'''
    pass
"""
        target = self._makeOne()
        result = target.modify(base, additional).dumps()
        expected = """\
def foo(x):
    '''new'''
    pass
"""
        self.assertEqual(expected.rstrip(), result.rstrip())

    def test_create_docstring(self):
        base = """\
def foo(x):
    return x + 1
"""
        additional = """\
def foo(x):
    '''updated'''
    pass
"""
        target = self._makeOne()
        result = target.modify(base, additional).dumps()
        expected = """\
def foo(x):
    '''updated'''
    return x + 1
"""
        self.assertEqual(expected.rstrip(), result.rstrip())

    def test_update_docstring(self):
        base = """\
def foo(x):
    '''new'''
    return x + 1
"""
        additional = """\
def foo(x):
    '''updated'''
    pass
"""
        target = self._makeOne()
        result = target.modify(base, additional).dumps()
        expected = """\
def foo(x):
    '''updated'''
    return x + 1
"""
        self.assertEqual(expected.rstrip(), result.rstrip())

    def test_add_decorator(self):
        base = """\
def foo(x):
    '''new'''
    return x + 1
"""
        additional = """\
@view_config(route_name='foo2')
def foo(x):
    '''updated'''
    pass
"""
        target = self._makeOne()
        result = target.modify(base, additional).dumps()
        expected = """\
@view_config(route_name='foo2')
def foo(x):
    '''updated'''
    return x + 1
"""
        self.assertEqual(expected.rstrip(), result.rstrip())

    def test_update_decorator(self):
        base = """\
@view_config(route_name='foo', renderer="foo.jinja2")
def foo(x):
    '''new'''
    return x + 1
"""
        additional = """\
@view_config(route_name='foo2')
def foo(x):
    '''updated'''
    pass
"""
        target = self._makeOne()
        result = target.modify(base, additional).dumps()
        expected = """\
@view_config(route_name='foo2', renderer="foo.jinja2")
def foo(x):
    '''updated'''
    return x + 1
"""
        self.assertEqual(expected.rstrip(), result.rstrip())
