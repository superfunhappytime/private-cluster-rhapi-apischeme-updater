# Project specific values
NAME?=private-cluster-rhapi-apischeme-updater
NAMESPACE?=private-cluster-rhapi-apischeme-updater

IMAGE_REGISTRY?=quay.io
IMAGE_REPOSITORY?=app-sre
IMAGE_NAME?=private-cluster-rhapi-apischeme-updater

VERSION_MAJOR?=0
VERSION_MINOR?=1
YAML_DIRECTORY?=deploy

TEMPLATE_DIR?=hack/templates/
GIT_ROOT?=$(shell git rev-parse --show-toplevel 2>&1)

# WARNING: REPO_NAME will default to the current directory if there are no remotes
# REPO_NAME?=$(shell basename $$((git config --get-regex remote\.*\.url 2>/dev/null | cut -d ' ' -f2 || pwd) | head -n1 | sed 's|.git||g'))
REPO_NAME?=private-cluster-rhapi-apischeme-updater

TEMPLATE_DESTINATION?=${GIT_ROOT}/hack/generated-templates/updater-template.yaml

IN_CONTAINER?=false

GEN_TEMPLATE=hack/generate_template.py -t ${TEMPLATE_DIR} -y ${YAML_DIRECTORY} -d ${TEMPLATE_DESTINATION} -r ${REPO_NAME}