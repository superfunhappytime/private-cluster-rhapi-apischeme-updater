SHELL := /usr/bin/env bash

DOCKERFILE = ./Dockerfile

# Include shared Makefiles
include project.mk
include standard.mk

default: generate-template docker-build

CONTAINER_ENGINE?=docker

.PHONY: docker-build
docker-build: build

.PHONY: generate-template
generate-template:
	if [ "${IN_CONTAINER}" == "true" ]; then \
		$(CONTAINER_ENGINE) run --rm -v `pwd -P`:`pwd -P` python:2.7.15 /bin/sh -c "cd `pwd`; pip install oyaml; `pwd`/${GEN_TEMPLATE}"; \
	else \
		${GEN_TEMPLATE}; \
	fi