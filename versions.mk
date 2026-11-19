# Runtime versions: .tool-versions is the only place where they are written.
# The Makefiles export them, docker-compose.yml passes them to the image builds
# as build arguments, and the CI reads them with `make -s versions`.
tool-version = $(shell awk '$$1 == "$(1)" {print $$2}' $(dir $(lastword $(MAKEFILE_LIST))).tool-versions)

export NODE_VERSION := $(call tool-version,nodejs)
export PYTHON_VERSION := $(call tool-version,python)
export UV_VERSION := $(call tool-version,uv)
