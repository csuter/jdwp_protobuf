#!/bin/bash

dir=$(dirname "$0")
dir=$(cd "$dir" && pwd)
cd "$dir/.."

# die on non-zero exit
set -e

function log {
  echo "$(date +"[%Y-%m-%d %H:%M:%S]") $@"
}

timestamp=$(date +%s)

# set up gen environment
rm -rf gen/
mkdir -p gen/{py,java,classes,proto,log}

stderr_log=gen/log/$timestamp.build.sh.err
stdout_log=gen/log/$timestamp.build.sh.out
last_err=last_err
last_out=last_out
exec > >(tee $stdout_log)
exec 2> >(tee $stderr_log)
ln -sf $stderr_log $last_err
ln -sf $stdout_log $last_out

log "Logging to $stdout_log and $stderr_log"

log "Coping source files to gen/"
cp -r src/* gen/

# build proto file from header and generated output
log "Generating JDWP proto definitions"
./gen/py/gen/jdwp_gen.py

log "Compiling protobuf proto defintions"
protoc \
  --proto_path=gen/proto \
  --python_out=gen/py/ \
  gen/proto/google/protobuf/descriptor.proto \

log "Compiling rpc proto defintions"
protoc \
  --proto_path=gen/proto \
  --python_out=gen/py \
  gen/proto/protobuf/socketrpc/rpc.proto \

log "Compiling proto defintions"
protoc \
  --proto_path=gen/proto \
  --python_out=gen/py \
  gen/proto/debug/jdwp/jdwp.proto \

log "Compiling java source code"
javac \
  -d gen/classes \
  -sourcepath src/java \
  @<(find gen/java -name '*.java')

log "Building jar"
cd gen/classes && jar -cf ../debug.jar com/ && cd ../../

log "Killing any running instances"
ps aux \
  | grep -v grep \
  | grep "test_server\|TestProgram" \
  | awk '{print $2}' \
  | xargs -n1 -i sh -c 'if [[ -n "{}" ]]; then kill -9 {}; fi'

log "Killing any swp files that got into gen/"
find gen/ -name '.*.sw*' | xargs rm -f

log "Done!"
