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

request = jdwp_pb2.VirtualMachine_Version_Request()

service  = jdwp_pb2.VirtualMachine_Stub(channel)
service.VirtualMachine_Version(controller, request, Callback())

if controller.failed():
	print "RPC ERROR(%s): %s" % (controller.reason, controller.error())
