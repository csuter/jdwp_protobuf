#!/bin/bash

dir=$(dirname "$0")
dir=$(cd "$dir" && pwd)

cd "$dir/.."

rm -r .classes 2>/dev/null
mkdir -p .classes

javac -d .classes -sourcepath src/java src/java/*.java
