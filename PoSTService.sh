#!/bin/sh

BASE=$( dirname -- "${BASH_SOURCE[0]}" )
source $BASE/.venv/bin/activate
$BASE/PoSTService.py
