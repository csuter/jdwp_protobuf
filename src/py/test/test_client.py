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

request = jdwp_pb2.VirtualMachine_ClassesBySignature_Request()
request.signature = "java.lang.String"

service  = jdwp_pb2.VirtualMachine_Stub(channel)
service.VirtualMachine_ClassesBySignature(controller, request, Callback())

if controller.failed():
	print "Rpc failed %s : %s" % (controller.error(), controller.reason)
