def includeme_swagger_router(config):
    config.add_route('pets', '/api/pets')
    config.add_route('pet', '/api/pets/{pet_id}')
    config.scan('.views')


def includeme(config):
    config.include(includeme_swagger_router)