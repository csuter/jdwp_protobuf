import socket
import struct
import sys
import traceback

import old.old_jdwp

class jdwp:
	def __init__(self, port = 5005):
		self.establish_connection(port)

		# dict of req_id -> (cmd_set, cmd)
		self.requests = dict()
		# dict of req_id -> reply
		self.replies = dict()

		# request ids are simply created sequentially starting with 0
		self.next_req_id = 0

		req_id = self.async_command(
				"VirtualMachine_Version",
				old.old_jdwp.cmd_specs["VirtualMachine_Version"][0],
				old.old_jdwp.cmd_specs["VirtualMachine_Version"][1],
				"")
		print(req_id)
		print(self.get_reply(req_id))


	def establish_connection(self, port):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect(('localhost', port))

		# handshake
		self.sock.send(b'JDWP-Handshake')
		data = self.sock.recv(14)
		if data != b'JDWP-Handshake':
			raise Exception('Failed handshake')

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
		if self.requests[req_id] in old.old_jdwp.cmd_specs:
			key = self.requests[req_id]
			_, err, data = self.replies[req_id]
			if err != 0:
				print("Error: " + str(err))
				traceback.print_tb(sys.exc_info()[2])
				return []
			# unpack_jdi_data returns (data, size). we just transfer the data part
			return old.old_jdwp.unpack_jdi_data(old.old_jdwp.cmd_specs[key][3], data)[0]
		return []

	def pop_reply(self, req_id):
		result = self.get_reply(req_id)
		del self.replies[req_id]
		del self.requests[req_id]
		return result

	def send(self, req_id, cmdset, cmd, data):
		flags = 0
		length = 11 + len(data)
		header = struct.pack(">IIBBB", length, req_id, flags, cmdset, cmd)
		self.sock.send(header)
		self.sock.send(data)

	def recv(self):
		header = jdwp.read_all(self.sock, 11)
		length, req_id, flags, err = struct.unpack('>IIBH', header)
		remaining = length - 11
		data = jdwp.read_all(self.sock, remaining)
		return req_id, flags, err, data

	@staticmethod
	def read_all(sock, num_bytes):
		msgparts = []
		remaining = num_bytes
		while remaining > 0:
			chunk = sock.recv(remaining)
			msgparts.append(chunk)
			remaining -= len(chunk)
		return b''.join(msgparts)

	def next_id(self):
		self.next_req_id += 1
		return self.next_req_id
