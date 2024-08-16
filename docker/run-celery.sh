#!/bin/sh

set -o errexit
set -o pipefail
set -o nounset

celery -A core worker --loglevel=INFO