#!/bin/bash

/entrypoint dag-processor&
nginx -g 'daemon off;'