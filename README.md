# semanticmatchservice
This is a simple Python application that listens on port 6006, with the apis detailed below. This application is using [docker-python-v3](https://git.corp.adobe.com/ASR/docker-python-v3) as base docker image.


## Software Requirements
### Operating System
- Ubuntu 20+

### Softwares
- Docker
- Python 3.8+
- VSCode (for debugging)

### apt-get packages
- software-properties-common
- build-essential
- cuda

## Hardware Requirements
- NVIDIA GPU (VRAM >= 24GB)

## How to run?
Following are the directions to run the service (specific to Unix and Windows operating systems):

### Set environment variables
Set following environment variables for running the service:
- ENVIRONMENT_NAME
- REGION_NAME
- SPLUNK_TOKEN
- REPLACE_NEWRELIC_APP
- REPLACE_NEWRELIC_LICENSE

Following variables are required during build process:
- ARTIFACTORY_UW2_USER
- ARTIFACTORY_UW2_API_TOKEN
- MODEL_PATH

Please refer to the [Local Development](https://wiki.corp.adobe.com/display/CTDxE/DxE+-+Anonymous+access+removal+in+Artifactory#DxE-AnonymousaccessremovalinArtifactory-LocalDevelopment) section of the Artifactory authentication wiki for instructions on setting the ARTIFACTORY_UW2_USER and ARTIFACTORY_UW2_API_TOKEN environment variables.

For Unix users,
```
export <ENV_VAR_NAME>=<ENV_VAR_VALUE>
```

### Docker commands(*Unix and Mac*)
To build the image with llm model, run:

```
make build
```

To run docker image container locally:
```
make run
```

To view container logs, run following command:
```
docker logs <container id>
```

Docker clean room setup:

To ensure that we're starting fresh (useful when you're doing a training session and/or trying to debug a local set up), it's best that we start with a 'clean room' and purge any local images and volumes that could introduce any potential 'contaminants' in our setup. You can read more on the following [wiki](https://wiki.corp.adobe.com/x/khu5TQ). Here is the command for docker clean room setup:

```
make clean-room
```

## How to debug?
Install all the dependencies using following command:
```
pip install -r requirements.txt
```

Download all the models using following command:
```
make download
```

Following are the directions to run the service in debug mode:
- Open the service folder in VSCode
- Go to Run & Debug tab on the left panel
- Select Debug option and click on run


## How to run Performance tests?
Run the following command to run locust service
```
locust -f tests/locust/performance.py
```

Launch Locust Web UI in your browser using following URL: http://localhost:8089


## 3rd Party Licenses
This product includes following third party software:
- [Mistral](LICENSE.mistral.md)
- [vLLM](LICENSE.vllm.md)