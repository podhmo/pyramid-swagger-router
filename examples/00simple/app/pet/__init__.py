def includeme_swagger_router(config):
    config.add_route('pet', '/pets')
    config.add_route('pet1', '/pets/{pet_id}')
    config.scan('.views')


def includeme(config):
    config.include(includeme_swagger_router)