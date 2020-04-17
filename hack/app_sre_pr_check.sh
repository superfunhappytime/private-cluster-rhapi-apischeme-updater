#!/bin/bash

set -exv

CURRENT_DIR=$(dirname "$0")

BASE_IMG="private-cluster-rhapi-apischeme-updater"
IMG="${BASE_IMG}:latest"

BUILD_CMD="docker build" IMG="$IMG" make docker-build