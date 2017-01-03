pyramid-swagger-router
========================================

view's code generation from a swagger's definition file.


motiviation
----------------------------------------

this package's motivation is below.

  Code generation is better than meta-programming, and onetime scaffold is simply bad.


Code generation is better than meta-programming
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Rational:

- Reading generated code is more easier than reading meta-programming code
- If you want to stop the code generation, just stop it (stopping using code generation is more easier than stopping meta-programming)

Onetime scaffold is simply bad
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Onetime scaffold (like a cookiecutter) is good for first creation. But, after scaffold implementation is changed, the migration about past generated code, handling manually(by yourself). So, this is bad.

It is ok, pyramid-swagger-router command called multiple times(because of merging code via FST(full syntax tree) (thunks to `redbaron <https://github.com/PyCQA/redbaron>`_)).

Where is the Router?
----------------------------------------

Nothing. This is the code generation tool for routing setting(including view configuration).

How to use
----------------------------------------

How to use this.

.. code-block:: bash

  $ pip install pyramid-swagger-router
  $ pyramid-swagger-router <swagger.yaml> <dst>


if you passing swagger.yaml such as below.

.. code-block:: yaml

  swagger: '2.0'
  info:
    title: Pet Shop Example API
    version: "0.1"
  consumes:
    - app.pet.views.ication/json
  produces:
    - app.pet.views.ication/json
  paths:
    /pets:
      x-pyramid-route-name: pets
      get:
        tags: [Pets]
        operationId: app.pet.views.get_pets
        summary: Get all pets
        parameters:
          - name: animal_type
            in: query
            type: string
            pattern: "^[a-zA-Z0-9]*$"
          - name: limit
            in: query
            type: integer
            minimum: 0
            default: 100
        responses:
          200:
            description: Return pets
            schema:
              type: array
              items:
                $ref: '#/definitions/Pet'
    /pets/{pet_id}:
      x-pyramid-route-name: pet
      get:
        tags: [Pets]
        operationId: app.pet.views.get_pet
        summary: Get a single pet
        parameters:
          - $ref: '#/parameters/pet_id'
        responses:
          200:
            description: Return pet
            schema:
              $ref: '#/definitions/Pet'
          404:
            description: Pet does not exist
      put:
        tags: [Pets]
        operationId: app.pet.views.put_pet
        summary: Create or update a pet
        parameters:
          - $ref: '#/parameters/pet_id'
          - name: pet
            in: body
            schema:
              $ref: '#/definitions/Pet'
        responses:
          200:
            description: Pet updated
          201:
            description: New pet created
      delete:
        tags: [Pets]
        operationId: app.pet.views.delete_pet
        summary: Remove a pet
        parameters:
          - $ref: '#/parameters/pet_id'
        responses:
          204:
            description: Pet was deleted
          404:
            description: Pet does not exist


  parameters:
    pet_id:
      name: pet_id
      description: Pet's Unique identifier
      in: path
      type: string
      required: true
      pattern: "^[a-zA-Z0-9-]+$"

  definitions:
    Pet:
      type: object
      required:
        - name
        - animal_type
      properties:
        id:
          type: string
          description: Unique identifier
          example: "123"
          readOnly: true
        name:
          type: string
          description: Pet's name
          example: "Susie"
          minLength: 1
          maxLength: 100
        animal_type:
          type: string
          description: Kind of animal
          example: "cat"
          minLength: 1
        tags:
          type: object
          description: Custom tags
        created:
          type: string
          format: date-time
          description: Creation time
          example: "2015-07-07T15:49:51.230+02:00"
          readOnly: true

output code are like these.

app/pet/__init__.py

.. code-block:: python

  def includeme_swagger_router(config):
      config.add_route('pets', '/pets')
      config.add_route('pet', '/pets/{pet_id}')
      config.scan('.views')


  def includeme(config):
      config.include(includeme_swagger_router)


app/pet/views.py

.. code-block:: python

  from pyramid.view import(
      view_config
  )


  @view_config(renderer='json', request_method='GET', route_name='pets')
  def get_pets(context, request):
      """
      Get all pets

      request.GET:

          * 'animal_type'  -  `{"type": "string", "pattern": "^[a-zA-Z0-9]*$"}`
          * 'limit'  -  `{"type": "integer", "minimum": 0, "default": 100}`
      """
      return {}


  @view_config(renderer='json', request_method='GET', route_name='pet')
  def get_pet(context, request):
      """
      Get a single pet

      request.matchdict:

          * 'pet_id'  Pet's Unique identifier  `{"type": "string", "required": true, "pattern": "^[a-zA-Z0-9-]+$"}`
      """
      return {}


  @view_config(renderer='json', request_method='PUT', route_name='pet')
  def put_pet(context, request):
      """
      Create or update a pet

      request.matchdict:

          * 'pet_id'  Pet's Unique identifier  `{"type": "string", "required": true, "pattern": "^[a-zA-Z0-9-]+$"}`

      request.json_body:

      ```
          {
            "type": "object",
            "required": [
              "name",
              "animal_type"
            ],
            "properties": {
              "id": {
                "type": "string",
                "description": "Unique identifier",
                "example": "123",
                "readOnly": true
              },
              "name": {
                "type": "string",
                "description": "Pet's name",
                "example": "Susie",
                "minLength": 1,
                "maxLength": 100
              },
              "animal_type": {
                "type": "string",
                "description": "Kind of animal",
                "example": "cat",
                "minLength": 1
              },
              "tags": {
                "type": "object",
                "description": "Custom tags"
              },
              "created": {
                "type": "string",
                "format": "date-time",
                "description": "Creation time",
                "example": "2015-07-07T15:49:51.230+02:00",
                "readOnly": true
              }
            }
          }
      ```
      """
      return {}


  @view_config(renderer='json', request_method='DELETE', route_name='pet')
  def delete_pet(context, request):
      """
      Remove a pet

      request.matchdict:

          * 'pet_id'  Pet's Unique identifier  `{"type": "string", "required": true, "pattern": "^[a-zA-Z0-9-]+$"}`
      """
      return {}

appendix 1
----------------------------------------

if you want to set custom route_name, using `x-pyramid-route-name`.

appendix 2
----------------------------------------

When desrialization from json request, `swagger-marshmallow-codegen <https://github.com/podhmo/swagger-marshmallow-codegen>`_ is helpful, maybe.
