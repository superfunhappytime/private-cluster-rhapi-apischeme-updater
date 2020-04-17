# Validate variables in project.mk exist
ifndef IMAGE_REGISTRY
$(error IMAGE_REGISTRY is not set; check project.mk file)
endif
ifndef IMAGE_REPOSITORY
$(error IMAGE_REPOSITORY is not set; check project.mk file)
endif
ifndef IMAGE_NAME
$(error IMAGE_NAME is not set; check project.mk file)
endif
ifndef VERSION_MAJOR
$(error VERSION_MAJOR is not set; check project.mk file)
endif
ifndef VERSION_MINOR
$(error VERSION_MINOR is not set; check project.mk file)
endif

# Generate version and tag information from inputs
COMMIT_NUMBER=$(shell git rev-list `git rev-list --parents HEAD | egrep "^[a-f0-9]{40}$$"`..HEAD --count)
CURRENT_COMMIT=$(shell git rev-parse --short=8 HEAD)
VERSION=$(VERSION_MAJOR).$(VERSION_MINOR).$(COMMIT_NUMBER)-$(CURRENT_COMMIT)

IMG?=$(IMAGE_REGISTRY)/$(IMAGE_REPOSITORY)/$(IMAGE_NAME):v$(VERSION)
IMAGE_URI=${IMG}
IMAGE_URI_LATEST=$(IMAGE_REGISTRY)/$(IMAGE_REPOSITORY)/$(IMAGE_NAME):latest
DOCKERFILE ?=./Dockerfile

default: build

.PHONY: isclean 
isclean:
	@(test "$(ALLOW_DIRTY_CHECKOUT)" != "false" || test 0 -eq $$(git status --porcelain | wc -l)) || (echo "Local git checkout is not clean, commit changes and try again." && exit 1)

.PHONY: build
build: isclean envtest
	docker build . -f $(DOCKERFILE) -t $(IMAGE_URI)
	docker tag $(IMAGE_URI) $(IMAGE_URI_LATEST)

.PHONY: push
push:
	docker push $(IMAGE_URI)
	docker push $(IMAGE_URI_LATEST)

.PHONY: envtest
envtest:
	@# test that the env target can be evaluated, required by osd-operators-registry
	@eval $$($(MAKE) env --no-print-directory) || (echo 'Unable to evaluate output of `make env`.  This breaks osd-operators-registry.' && exit 1)

.PHONY: test
test: envtest

.PHONY: env
.SILENT: env
env: isclean
	echo NAME=$(NAME)
	echo NAMESPACE=$(NAMESPACE)
	echo VERSION=$(VERSION)
	echo IMAGE_URI=$(IMAGE_URI)
