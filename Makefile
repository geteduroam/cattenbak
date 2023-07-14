AWS_PROFILE :=
AWS_REGION := eu-central-1
S3_URL := s3://geteduroam-disco/v1-test/discovery.json
LAMBDA_FUNCTION := cattenbak


cattenbak/cattenbak.py: cattenbak/i18n.py cattenbak cattenbak.py
	cp cattenbak.py cattenbak/


cattenbak/i18n.py: i18n.py cattenbak
	cp i18n.py cattenbak/


cattenbak: requirements.txt
	rm -rf cattenbak
	pip3 install -r requirements.txt -t ./cattenbak/
	find ./cattenbak/ -name \*.so -delete
	touch -c cattenbak


cattenbak.zip: lambda_function.py cattenbak/cattenbak.py
	cp lambda_function.py cattenbak/
	cd cattenbak; rm -rf ../cattenbak.zip; zip -9 -r ../cattenbak.zip .


discovery.json: cattenbak/cattenbak.py
	curl --compressed -sSLO https://discovery.eduroam.app/v2/discovery.json || true
	cattenbak/cattenbak.py --file-path discovery.json


discovery.json.gz: discovery.json
	gzip -9c discovery.json >discovery.json.gz


run: cattenbak/cattenbak.py
	cattenbak/cattenbak.py
.PHONY: run


upload: discovery.json.gz
	aws --profile '$(AWS_PROFILE)' s3 \
		cp discovery.json.gz '$(S3_URL)' \
		--content-encoding gzip \
		--acl public-read \
		--cache-control "public, max-age=900, s-maxage=300, stale-while-revalidate=86400, stale-if-error=2592000"
.PHONY: upload


deploy: cattenbak.zip
	aws --region '$(AWS_REGION)' --profile '$(AWS_PROFILE)' lambda \
		update-function-code --function-name $(LAMBDA_FUNCTION) --zip-file fileb://cattenbak.zip
	@echo
	@echo Please test the deployed function on the following URL:
	@echo
	@echo '	https://$(AWS_REGION).console.aws.amazon.com/lambda/home?region=$(AWS_REGION)#/functions/$(LAMBDA_FUNCTION)?tab=testing'
	@echo
.PHONY: deploy


clean:
	rm -rf cattenbak cattenbak.zip discovery.json discovery.json.gz
.PHONY: clean


camera-ready:
	python3 -m mypy cattenbak.py lambda_function.py
.PHONY: camera-ready
