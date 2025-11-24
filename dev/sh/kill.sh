#!/usr/bin/env bash

# Copyright (c) 2021-2024 Datalayer, Inc.
#
# Datalayer License

uname_out="$(uname -s)"

case "${uname_out}" in
    Linux*)     export OS=LINUX;;
    Darwin*)    export OS=MACOS;;
#    CYGWIN*)    OS=CYGWIND;;
#    MINGW*)     OS=MINGW;;
    *)          export OS="UNSUPPORTED:${unameOut}"
esac

function kill_port() {
    case "${OS}" in
        LINUX)     fuser -k $1/tcp;;
        MACOS)     lsof -i TCP:$1 | grep LISTEN | awk '{print $2}' | xargs kill -9;;
        *)         echo "Unsupported operating system ${OS}"
    esac    
}

kill_port 2181
kill_port 2200
kill_port 3063
kill_port 4400
kill_port 6600
kill_port 6650
kill_port 7000
kill_port 7667
kill_port 8080
kill_port 8098
kill_port 8200
kill_port 8888
kill_port 9092
kill_port 8686
kill_port 8888
kill_port 8983
kill_port 9300
kill_port 9500
kill_port 9600
kill_port 9700
kill_port 9800
kill_port 9900
