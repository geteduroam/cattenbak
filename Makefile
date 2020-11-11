disco/v1: src/eduroam/cat etc/cattenbak.conf.php
	mkdir -p disco/v1
	php -d memory_limit=1023M bin/generate.php

prod: disco/v1
	git pull --autostash --rebase
	git commit -m"Bump serial.txt to $$(cat serial.txt)" serial.txt || true
	aws --profile geteduroam s3 cp disco/v1/discovery-$$(cat serial.txt).json.gz s3://eduroam-discovery/discovery/v1/discovery.json --cache-control "public, max-age=3600, stale-while-revalidate=86400, stale-if-error=2592000" --content-encoding gzip
	git push

camera-ready: src/eduroam/cat syntax codestyle phpunit psalm phan

clean:
	rm -rf disco composer.phar php-cs-fixer-v2.phar psalm.phar phpunit-7.phar vendor
	find $$(php -r 'echo sys_get_temp_dir();') -name eduroam-\* -delete

test: syntax phpunit

composer.phar:
	curl -sSLO https://getcomposer.org/composer.phar || wget https://getcomposer.org/composer.phar

php-cs-fixer-v2.phar:
	curl -sSLO https://cs.sensiolabs.org/download/php-cs-fixer-v2.phar || wget https://cs.sensiolabs.org/download/php-cs-fixer-v2.phar

psalm.phar:
	curl -sSLO https://github.com/vimeo/psalm/releases/download/3.9.5/psalm.phar || wget https://github.com/vimeo/psalm/releases/download/3.9.5/psalm.phar

phpunit-7.phar:
	curl -sSLO https://phar.phpunit.de/phpunit-7.phar || wget https://phar.phpunit.de/phpunit-7.phar

phan.phar:
	curl -sSLO https://github.com/phan/phan/releases/download/2.6.0/phan.phar || wget https://github.com/phan/phan/releases/download/2.6.0/phan.phar

vendor: composer.phar
	php composer.phar install

psalm: psalm.phar src/eduroam/cat etc/cattenbak.conf.php
	mkdir -p vendor
	ln -s ../src/_autoload.php vendor/autoload.php || true
	php psalm.phar

phan: phan.phar
	php phan.phar --allow-polyfill-parser

codestyle: php-cs-fixer-v2.phar
	php php-cs-fixer-v2.phar fix

phpunit: phpunit-7.phar
	php phpunit-7.phar

syntax:
	find . ! -path './vendor/*' ! -path './lib/*' -name \*.php -print0 | xargs -0 -n1 php -l

src/eduroam/cat: lib/git.sr.ht/eduroam/php-cat-client/src
	cp -a lib/git.sr.ht/eduroam/php-cat-client/src/eduroam/cat src/eduroam/

lib/git.sr.ht/eduroam/php-cat-client/src:
	git submodule init
	git submodule update

.PHONY: prod camera-ready codestyle psalm phan phpunit phpcs clean syntax test
