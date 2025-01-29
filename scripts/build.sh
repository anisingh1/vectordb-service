#!/bin/bash -e

if [ -f '.env' ]
then
    source .env
fi

set -e
echo "Using virtualenv "${PYTHON_VIRTUAL_ENV_FOLDER}""
cp pip.conf ${PYTHON_VIRTUAL_ENV_FOLDER}

export PYTHONPATH=`pwd`/app

if [ $BUILD_TYPE != "pip_install" ]; then
    . ${PYTHON_VIRTUAL_ENV_FOLDER}/bin/activate
fi

if [ $BUILD_TYPE = "pip_install" ]; then
    echo "Building artifacts ..."
    python3 -m venv ${PYTHON_VIRTUAL_ENV_FOLDER}
    . ${PYTHON_VIRTUAL_ENV_FOLDER}/bin/activate
    pip3 install --upgrade pip
    export PIP_INDEX_URL=https://${ARTIFACTORY_UW2_USER}:${ARTIFACTORY_UW2_API_TOKEN}@artifactory-uw2.adobeitc.com/artifactory/api/pypi/pypi-asr-python-release-local/simple && \
    pip3 install -r requirements.txt
    #pip3 install flash-attn
else
    echo "Unknown BUILD_TYPE:$BUILD_TYPE"
    exit 1
fi