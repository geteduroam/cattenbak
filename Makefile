cattenbak/cattenbak.py: cattenbak cattenbak.py
	cp cattenbak.py cattenbak/
	chmod +x cattenbak/cattenbak.py

cattenbak: requirements.txt
	pip3 install -r requirements.txt -t ./cattenbak/
	touch cattenbak

run: cattenbak/cattenbak.py
	cattenbak/cattenbak.py
.PHONY: run

clean:
	rm -rf cattenbak
.PHONY: clean
