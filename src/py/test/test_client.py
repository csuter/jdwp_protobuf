#!/usr/bin/python2

import jdwp_pb2
import protobuf.socketrpc
import google.protobuf.text_format as pbtf

class Callback:
	def run(self,response):
		print "Received Response: %s" % response

hostname = "localhost"
port = 10001
channel = protobuf.socketrpc.channel.SocketRpcChannel(hostname,port)
controller = channel.newController()

service = jdwp_pb2.VirtualMachine_Stub(channel)

#request = jdwp_pb2.VirtualMachine_Version_Request()
#service.VirtualMachine_Version(controller, request, Callback())
#if controller.failed():
#	print "RPC ERROR(%s): %s" % (controller.reason, controller.error())

request = jdwp_pb2.VirtualMachine_ClassesBySignature_Request()
request.signature = ""
service.VirtualMachine_ClassesBySignature(controller, request, Callback())
if controller.failed():
	print "RPC ERROR(%s): %s" % (controller.reason, controller.error())
