default: ci

# The image tag for ci will be different with BYOJ, see https://jira.corp.adobe.com/browse/EON-4685
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

IMAGE_NAME=vectordb
ARTIFACTORY_DOWNLOAD=docker-asr-release
ARTIFACTORY_UPLOAD=docker-g11n-content-release
DOCKER_ID=$(notdir $(MODEL_PATH))

login:
ifeq ($(ARTIFACTORY_UW2_USER), )
	@echo "make sure that ARTIFACTORY_UW2_USER is set appropriately in your environment"
	exit 1
endif
ifeq ($(ARTIFACTORY_UW2_API_TOKEN), )
	@echo "make sure that ARTIFACTORY_UW2_API_TOKEN is set appropriately in your environment"
	exit 1
endif
	@echo docker login -u ARTIFACTORY_UW2_USER -p ARTIFACTORY_UW2_API_TOKEN $(ARTIFACTORY_DOWNLOAD).dr-uw2.adobeitc.com
	@docker login -u $(ARTIFACTORY_UW2_USER) -p $(ARTIFACTORY_UW2_API_TOKEN) $(ARTIFACTORY_DOWNLOAD).dr-uw2.adobeitc.com
	@docker login -u $(ARTIFACTORY_UW2_USER) -p $(ARTIFACTORY_UW2_API_TOKEN) $(ARTIFACTORY_UPLOAD).dr-uw2.adobeitc.com

.PHONY: build

checkdocker:
	@sh ./scripts/checkdocker.sh

download:
	@sh ./scripts/download.sh $(MODEL_PATH) $(ARTIFACTORY_UW2_API_TOKEN)

build: checkdocker login download
	docker build --no-cache --build-arg MODEL_PATH --build-arg ARTIFACTORY_UW2_USER --build-arg ARTIFACTORY_UW2_API_TOKEN --pull -t $(IMAGE_NAME) .
	echo "Success"

clean-room: checkdocker
	@sh ./scripts/clean-room.sh

run: checkdocker
	docker run --rm --gpus all -e ENVIRONMENT_NAME=$(ENVIRONMENT_NAME) -e REGION_NAME=$(REGION_NAME) -p 6006:6006 $(IMAGE_NAME)

upload: checkdocker login
	$(eval IMAGE_ID := $(shell docker images --filter=reference=$(IMAGE_NAME) --format={{.ID}}))
	docker tag $(IMAGE_ID) $(ARTIFACTORY_UPLOAD).dr-uw2.adobeitc.com/$(IMAGE_NAME):$(DOCKER_ID)
	docker push $(ARTIFACTORY_UPLOAD).dr-uw2.adobeitc.com/$(IMAGE_NAME):$(DOCKER_ID)
	docker rmi $(ARTIFACTORY_UPLOAD).dr-uw2.adobeitc.com/$(IMAGE_NAME):$(DOCKER_ID)
	echo "$(ARTIFACTORY_UPLOAD).dr-uw2.adobeitc.com/$(IMAGE_NAME):$(DOCKER_ID)"
