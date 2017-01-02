default: clean
	cp parts/*.py app/
	pyramid-swagger-router swagger.yaml .

run:
	PYTHONPATH=. python app/__init__.py

clean:
	rm -fr app/*.py
