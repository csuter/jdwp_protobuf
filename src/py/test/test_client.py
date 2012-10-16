#!/usr/bin/python2

import jdwp_pb2
import protobuf.socketrpc
import google.protobuf.text_format as pbtf
import logging

classes_response = []

hostname = "localhost"
port = 10001

channel = protobuf.socketrpc.channel.SocketRpcChannel(hostname,port)
controller = channel.newController()

virtual_machine_service = jdwp_pb2.VirtualMachine_Stub(channel)	
event_request_service = jdwp_pb2.EventRequest_Stub(channel)
event_service = jdwp_pb2.Event_Stub(channel)

class PrintItCallback:
	def run(self, result):
		print("result: %s" % result)

request = jdwp_pb2.VirtualMachine_AllClasses_Request()
virtual_machine_service.VirtualMachine_AllClasses(controller, request, PrintItCallback())

#event_set_request = jdwp_pb2.EventRequest_Set_Request()
#event_set_request.eventKind = jdwp_pb2.EventKind_BREAKPOINT
#event_set_request.suspendPolicy = jdwp_pb2.SuspendPolicy_EVENT_THREAD
#mod = event_set_request.modifiers.add()
#mod.modKind = 6 # ClassMatch
#mod.ClassMatch.classPattern = "*TestProgram*"
#
#class EventRequestCallback:
#	def run(self, response):
#		print("response: %s" % response)
#
#event_request_service.EventRequest_Set(controller, event_set_request, EventRequestCallback())
#
#if controller.failed():
#	print "RPC ERROR(%s): %s" % (controller.reason, controller.error())
