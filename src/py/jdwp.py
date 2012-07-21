import socket
import struct
import sys
import traceback
from jdwp_constants import *
from jdwp_util import *

class jdwp:

	def __init__(self, port = 5005):

		self.spec = parse_jdwp_spec(
				"/home/cgs/code/debug/tmp/spec",
				lambda x, y, z : self.command_set_handler(x, y, z),
				lambda x, y, z : self.constant_set_handler(x, y, z))

		exit(1)

		self.establish_connection(port)

		# dict of req_id -> (cmd_set, cmd)
		self.requests = dict()
		# dict of req_id -> reply
		self.replies = dict()

		# request ids are simply created sequentially starting with 0
		self.next_req_id = 0
		
		self.version_info = self.get_reply(self.vm_version())
		self.id_size_info = self.get_reply(self.vm_id_sizes())

	def establish_connection(self, port):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect(('localhost', port))

		# handshake
		self.sock.send(bytes('JDWP-Handshake', 'UTF-8'))
		data = self.sock.recv(14)
		if data != b'JDWP-Handshake':
			raise Exception('Failed handshake')

	def command_set_handler(self, text, bytepos, parsetree):
		print(parsetree)

	def constant_set_handler(self, text, bytepos, parsetree):
		1#print(parsetree[0])

	def func_creator(self, name, cmdset, cmd, packing_str, sync=False):
		if sync:
			return lambda self, args=() : self.get_reply(self.async_command(name, cmdset, cmd, pack_jdi_data(packing_str, args)))
		return lambda self, args=() : self.async_command(name, cmdset, cmd, pack_jdi_data(packing_str, args))

	def async_command(self, name, cmd_set, cmd, data):
		req_id = self.next_id()
		self.requests[req_id] = name
		self.send(req_id, cmd_set, cmd, data)
		return req_id

	def get_reply(self, req_id):
		if req_id not in self.replies:
			while req_id not in self.replies:
				reply_id, flags, err, data = self.recv()
				self.replies[reply_id] = (flags, err, data)
		if self.requests[req_id] in cmd_specs:
			key = self.requests[req_id]
			_, err, data = self.replies[req_id]
			if err != 0:
				print("Error: " + str(err))
				traceback.print_tb(sys.exc_info()[2])
				return []
			# unpack_jdi_data returns (data, size). we just transfer the data part
			return unpack_jdi_data(cmd_specs[key][3], data)[0]
		return []

	def pop_reply(self, req_id):
		result = self.get_reply(req_id)
		del self.replies[req_id]
		del self.requests[req_id]
		return result

	def send(self, req_id, cmdset, cmd, data):
		flags = 0
		msg = bytearray()
		length = 11 + len(data)
		msg.extend(struct.pack('>IIBBB',
			length, req_id, flags, cmdset, cmd))
		msg.extend(data)
		print("SEND header = %s, msg = %s" % (struct.unpack('>IIBBB', msg[0:11]), msg))
		self.sock.send(msg)

	def recv(self):
		header = read_all(self.sock, 11)
		length, req_id, flags, err = struct.unpack('>IIBH', header)
		msgparts = []
		remaining = length - 11
		data = read_all(self.sock, remaining)
		print("RECV header = %s, data = %s" % (struct.unpack('>IIBH', header), data))
		return req_id, flags, err, data

	def next_id(self):
		self.next_req_id += 1
		return self.next_req_id
