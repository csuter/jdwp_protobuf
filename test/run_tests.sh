#!/bin/bash

set -e

dir=$(dirname "$0")
dir=$(cd "$dir" && pwd)

cd "$dir"

# We need
#  1) a running java process
#  2) a running vim instance in server mode
#  3) a running python debug server instance attached to the vim server and the target jvm

../bin/build.sh

java -classpath ../.classes testprog

# start a vim instance in a separate gnome-terminal window
gnome-terminal -e "bash -c 'vim --servername test123'"

