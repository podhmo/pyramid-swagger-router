default: clean
	cp *.py app/
	pyramid-swagger-router swagger.yaml ./app

run:
	PYTHONPATH=. python app/__init__.py

clean:
	rm -fr app/*.py
