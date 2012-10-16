
import collections
import logging
import socket
import struct
import sys
import time
import traceback

import google.protobuf.descriptor
import jdwp_impl

import threading

class Jdwp:
	def __init__(self, port = 5005):
		self.establish_connection(port)
		# dict of req_id -> (cmd_set, cmd)
		self.requests = dict()
		# dict of req_id -> reply
		self.replies = dict()
		# request ids are simply created sequentially starting with 0
		self.next_req_id = 0

		# Initialize event listener
		self.reader_thread_ = EventListenerThread()
		self.reader_thread_.jdwp_ = self
		self.reader_thread_.start()

	def establish_connection(self, port):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		retries = 5
		while retries > 0:
			retries -= 1
			try:
				self.sock.connect(('localhost', port))
				break
			except Exception, e:
				logging.exception(e)
				logging.error("Connection failed. Retrying %d times" % retries)
				time.sleep(1)
		# handshake
		self.sock.send(b'JDWP-Handshake')
		data = self.sock.recv(14)
		if data != b'JDWP-Handshake':
			raise Exception('Failed handshake')

	def call(self, name, cmd_set, cmd, data):
		return self.pop_reply(self.call_async(name, cmd_set, cmd, data))

	def call_async(self, name, cmd_set, cmd, data):
		req_id = self.next_id()
		self.requests[req_id] = name
		packed_data = pack_jdi_data(jdwp_impl.COMMAND_SPECS[name][2], data)
		self.send(req_id, cmd_set, cmd, packed_data)
		return req_id

	def get_reply(self, req_id):
		if req_id not in self.replies:
			while req_id not in self.replies:
				1
		if self.requests[req_id] in jdwp_impl.COMMAND_SPECS:
			key = self.requests[req_id]
			_, err, data = self.replies[req_id]
			if err != 0:
				raise Exception("JDWP Error(%s=%d): \"%s\"" % (
						ERROR_MESSAGES[err][0], err, ERROR_MESSAGES[err][1]))
			return unpack_jdi_data(jdwp_impl.COMMAND_SPECS[key][3], data)[0]
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
		print("Sending length:%s, req_id:%s, flags:%s, cmdset:%s, cmd:%s, data:%s" %(
				length, req_id, flags, cmdset, cmd, data))
		self.sock.send(header)
		self.sock.send(data)

	def recv(self):
		header = read_all(self.sock, 11)
		length, req_id, flags, err = struct.unpack('>IIBH', header)
		remaining = length - 11
		data = read_all(self.sock, remaining)
		return req_id, flags, err, data

	def next_id(self):
		self.next_req_id += 1
		return self.next_req_id


def read_all(sock, num_bytes):
	msgparts = []
	remaining = num_bytes
	while remaining > 0:
		chunk = sock.recv(remaining)
		msgparts.append(chunk)
		remaining -= len(chunk)
	return b''.join(msgparts)


def unpack_jdi_data(fmt, data):
	result = []
	pos = 0
	in_paren = 0
	size = 0
	idx = 0
	while idx < len(fmt):
		c = fmt[idx]
		if in_paren > 0:
			if c == '(':
				in_paren += 1
			elif c == ')':
				in_paren -= 1
			idx += 1
			continue
		if c == 'S':
			strlen = struct.unpack(">I", data[pos:pos+4])[0]
			result.append(struct.unpack(str(strlen) + "s",
					data[pos+4:pos+strlen+4])[0].decode('UTF-8'))
			size += 4 + strlen
			pos += 4 + strlen
		elif c == 'I':
			result.append(struct.unpack(">I", data[pos:pos+4])[0])
			size += 4
			pos += 4
		elif c == 'b':
			result.append(struct.unpack(">B", data[pos:pos+1])[0] != 0)
			size += 1
			pos += 1
		elif c == 'B':
			result.append(struct.unpack(">B", data[pos:pos+1])[0])
			size += 1
			pos += 1
		elif c == 'L':
			result.append(struct.unpack(">Q", data[pos:pos+8])[0])
			size += 8
			pos += 8
		elif c == 'V':
			value, value_size = parse_jdi_value(data)
			result.append(value)
			size += value_size
			pos += value_size
		elif c == 'T':
			type_tag, object_id = struct.unpack(">BQ", data[pos:pos+9])
			result.append((type_tag, object_id))
			size += 9
			pos += 9
		elif c == 'X':
			type_tag, class_id, method_id, index = struct.unpack(">BQQQ", data[pos:pos+25])
			result.append((type_tag, class_id, method_id, index))
			size += 25
			pos += 25
		elif c == 'A':
			raise Exception("IMPLEMENT ARRAY REGION UNPACKING")
		#elif c == '?':
		elif c == 'R':
			num = struct.unpack(">I", data[pos:pos+4])[0]
			pos += 4
			sub_result = []
			if fmt[idx+1] != '(':
				raise Exception("jdi_data fmt exception: expect '(' after 'R'")
			close_paren = find_close_paren(fmt, idx+1)
			if close_paren == -1:
				raise Exception("jdi_data fmt exception: no matching ')'")
			sub_data_fmt = fmt[idx+2:close_paren]
			for i in range(num):
				sub_data, sub_size = unpack_jdi_data(sub_data_fmt, data[pos:])
				pos += sub_size
				size += sub_size
				sub_result.append(sub_data)
			result.append(sub_result)
		elif c == '(':
			in_paren = 1
		idx += 1
	return result, size


def parse_jdi_value(data):
	tag = struct.unpack(">B", data[0])
	data_size = tag_constants_data_sizes[tag]
	fmt = ">" + "B" * data_size
	data = struct.unpack(fmt, data[1:])
	return (tag, data), 1 + data_size


def find_close_paren(string, start):
	count = 1
	if string[start] == '(':
		idx = start + 1
	else:
		idx = start
	while count > 0:
		if string[idx] == '(':
			count += 1
		elif string[idx] == ')':
			count -= 1
		idx += 1
	return idx-1


def pack_jdi_data(fmt, data):
	result = bytearray()
	pos = 0
	in_paren = 0
	idx = 0
	while idx < len(fmt):
		c = fmt[idx]
		if in_paren > 0:
			if c == '(':
				in_paren += 1
			elif c == ')':
				in_paren -= 1
			idx += 1
			continue
		elif c == 'B':
			# write string length
			result.extend(struct.pack(">B", data[pos]))
			pos += 1
		elif c == 'b':
			# write string length
			result.extend(struct.pack(">B", data[pos]))
			pos += 1
		elif c == 'I':
			# write string length
			result.extend(struct.pack(">I", data[pos]))
			pos += 1
		elif c == 'L':
			# write string length
			result.extend(struct.pack(">Q", data[pos]))
			pos += 1
		elif c == 'S':
			strlen = len(data[pos])
			# write string length
			result.extend(struct.pack(">I", strlen))
			result.extend(bytearray(data[pos][0],"UTF-8"))
			pos += 1
		elif c == 'A':
			raise Exception("IMPLEMENT ARRAY REGION PACKING")
		elif c == '?':
			type_tag, rest = data
			type_tag_fmt = fmt[idx+1:idx+2]
			result.extend(pack_jdi_data(type_tag_fmt, type_tag))
			sub_data_fmt = get_paren_substr_after(fmt, idx+1)
			clauses = dict((int(k), v) for (k, v) in (x.split("=") for x in sub_data_fmt.split("|")))
			result.extend(pack_jdi_data(clauses[type_tag[0]], rest))
			idx += 1
			pos += 1
		elif c == 'R':
			num = len(data[pos])
			result.extend(struct.pack(">I", num))
			sub_result = bytearray()
			sub_data_fmt = get_paren_substr_after(fmt, idx)
			for i in range(num):
				sub_data = pack_jdi_data(sub_data_fmt, data[pos][i])
				sub_result.extend(sub_data)
			pos += 1
			result.extend(sub_result)
		elif c == '(':
			in_paren = 1
		else:
			raise Exception("Unrecognized fmt char %s at idx %s in fmt \"%s\" for data \"%s\"" % (
					c, idx, fmt, data))
		idx += 1
	return result

def proto_to_data(proto):
	fields = []
	if hasattr(proto, '_fields'):
		for field in proto._fields:
			value = proto._fields[field]
			print("field.name: %s, value: %s" % (field.name, value))
			if field.label == 3:
				data = [ proto_to_data(entry) for entry in value ]
			else:
				data = proto_to_data(value)
			fields.append((field.number, data))
		fields = [ entry[1] for entry in sorted(fields, key = lambda k:k[0]) ]
	else:
		fields = [ proto ]
	return fields

def get_paren_substr_after(fmt, idx):
	if fmt[idx+1] != '(':
		raise Exception("jdi_data fmt exception: expected '(' at %d of '%s'" % (idx, fmt))
	close_paren = find_close_paren(fmt, idx+1)
	if close_paren == -1:
		raise Exception("jdi_data fmt exception: no matching ')' for paren at %d of '%s'" % (idx, fmt))
	return fmt[idx+2:close_paren]

class EventListenerThread(threading.Thread):

	def run(self):
		print("EventListenerThread active")
		while True:
			reply_id, flags, err, data = self.jdwp_.recv()
			print("Received reply: %s" % [reply_id, flags, err, data])
			self.jdwp_.replies[reply_id] = (flags, err, data)

with open("data/errors", 'r') as f: ERROR_MESSAGE_LINES = [
		line.strip().split("\t") for line in f.readlines() ]

ERROR_MESSAGES = dict([ (int(line[0]), line[1:]) for line in ERROR_MESSAGE_LINES ])

