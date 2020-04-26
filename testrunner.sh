#!/bin/bash

USAGE="testrunner.sh [testfile] [watchfile]"
TESTFILE=""
WATCHFILE=""


if [[ -z $1 ]]; then
    echo $USAGE
    exit 1
else
    TESTFILE=$1
fi

if [[ -z $2 || ! -e $2 ]]; then
    echo $USAGE
    exit 1
else
    WATCHFILE=$2
fi

LASTMD5=0

while [ 1 ]; do 
    MDFIVE=$(md5sum $WATCHFILE)
    if [[ $LASTMD5 == $MDFIVE ]]; then
	sleep 1
    else
	clear
	sudo python3 -m unittest $TESTFILE
	LASTMD5=$MDFIVE
	sleep 1
    fi
done

