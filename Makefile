usage:
	@echo 'Usage: make { run | cattenbak | clean }'
	@echo '	make run       : Run one-off'
	@echo '	make cattenbak : Create Python bundle in '"'"cattenbak"'" directory
	@echo '	make clean     : Remove generated files
.PHONY: usage

run: cattenbak
	cattenbak/cattenbak.py
.PHONY: run

clean:
	rm -rf cattenbak
.PHONY: clean

cattenbak: cattenbak.py
	pip3 install -r requirements.txt -t ./cattenbak/
	cp cattenbak.py cattenbak/
	chmod +x cattenbak/cattenbak.py
	touch cattenbak
