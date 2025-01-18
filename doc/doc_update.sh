#!/bin/sh
#
# Script para tualização da documentação

uv export --no-dev --no-hashes -o requirements.txt
uv export --no-hashes -o requirements-dev.txt

uv run pdoc --html ./apisbr -o doc -f