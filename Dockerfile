# Please update your base container regularly for bug fixes and security patches.
# See https://git.corp.adobe.com/adobe-platform/bbc-factory for the latest BBC releases.
FROM docker-asr-release.dr-uw2.adobeitc.com/asr/python_v3:14.1.0 AS builder
ENV BUILD_TYPE=pip_install
ARG ARTIFACTORY_UW2_USER
ARG ARTIFACTORY_UW2_API_TOKEN

RUN apt-get update && apt-get upgrade -y && apt-get install --no-install-recommends -y software-properties-common git git-lfs build-essential python3-dev && mkdir /build
WORKDIR /build

COPY ./pip.conf ./pip.conf
COPY ./app ./app
COPY ./container ./container
COPY ./scripts ./scripts
COPY ./requirements.txt ./requirements.txt

WORKDIR /build
RUN chmod +x ./scripts/build.sh
RUN ./scripts/build.sh

# Please update your base container regularly for bug fixes and security patches.
# See https://git.corp.adobe.com/adobe-platform/bbc-factory for the latest BBC releases.
FROM docker-asr-release.dr-uw2.adobeitc.com/asr/python_v3:14.1.0
EXPOSE 6006
ARG MODEL_PATH

COPY --from=builder /build/pip.conf ${PYTHON_VIRTUAL_ENV_FOLDER}
COPY --from=builder ${PYTHON_VIRTUAL_ENV_FOLDER} ${PYTHON_VIRTUAL_ENV_FOLDER}
COPY --chown=asruser --from=builder /build/app ${PYTHON_APP_FOLDER}
COPY --chown=asruser ${MODEL_PATH} ${PYTHON_APP_FOLDER}/model

# S6 Files
COPY --from=builder --chown=asruser /build/container/root /
WORKDIR ${PYTHON_APP_FOLDER}
USER ${NOT_ROOT_USER}