cattenbak/cattenbak.py: cattenbak cattenbak.py
	cp cattenbak.py cattenbak/

cattenbak: requirements.txt
	rm -rf cattenbak
	pip3 install -r requirements.txt -t ./cattenbak/
	touch cattenbak

cattenbak.zip: lambda_function.py cattenbak/cattenbak.py
	cp lambda_function.py cattenbak/
	cd cattenbak; rm -rf ../cattenbak.zip; zip -9 -r ../cattenbak.zip .

run: cattenbak/cattenbak.py
	cattenbak/cattenbak.py
.PHONY: run

clean:
	rm -rf cattenbak
.PHONY: clean
