#!/bin/sh

BASE=$( dirname -- "${BASH_SOURCE[0]}" )
source $BASE/.venv/bin/activate

WOLFRAM_APPID_FILE=$HOME/.config/PoSTServices/Wolfram.appid
export WOLFRAM_APPID=$([[ -e $WOLFRAM_APPID_FILE ]] && cat $WOLFRAM_APPID_FILE )

XMODIFIERS= $BASE/PoSTService.py
