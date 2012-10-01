#!/usr/bin/python2

# Import required RPC modules
import protobuf.socketrpc.server
import jdwp
import jdwp_pb2
import jdwp_impl

# Create and register the service
# Note that this is an instantiation of the implementation class,
# *not* the class defined in the proto file.
jdwp = jdwp.jdwp()

virtual_machine = jdwp_impl.VirtualMachineImpl(jdwp)
server = protobuf.socketrpc.server.SocketRpcServer(10001)
server.registerService(virtual_machine)

# Start the server
print('Serving on port 10001')
server.run()
