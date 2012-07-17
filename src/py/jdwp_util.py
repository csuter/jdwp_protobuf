import struct
import re

from pyparsing import *

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
			result.append(struct.unpack(str(strlen) + "s", data[pos+4:pos+strlen+4])[0].decode('UTF-8'))
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


packers = dict()
packers['S'] = lambda data : struct.pack(">I", len(data)).extend(bytearray(data), 'UTF-8')
packers['I'] = lambda data : struct.pack(">I", data)
packers['b'] = lambda data : struct.pack(">B", data)
packers['B'] = lambda data : struct.pack(">B", data)
packers['L'] = lambda data : struct.pack(">Q", data)
packers['V'] = lambda data : struct.pack(">B", data[0]).extend(
		struct.pack(">" + "B"*tag_constants_data_sizes[data[0]], data[1]))
packers['T'] = lambda data : struct.pack(">B", data[0]).extend(
		struct.pack(">Q", data[1]))
packers['X'] = lambda data : struct.pack(">B", data[0]).extend(
		struct.pack(">Q", data[1])).extend(
		struct.pack(">Q", data[2])).extend(
		struct.pack(">Q", data[3]))

def parse_jdwp_spec(specfile):
	print("START")
	f = open(specfile, 'r')
	spec = f.read()
	end_of_comment = spec.find("*/")
	spec = spec[end_of_comment+40:]
	spec = re.sub(r'\s+', r' ', spec)
	spec = re.sub(r'" "', r' ', spec)
	spec = re.sub(r'\s+', r' ', spec)
	spec = re.sub(r'\(\s+', r'(', spec)
	spec = re.sub(r'\s+\)', r')', spec)
	print(spec)
	print(len(spec))
	exit(1)

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
		elif c == 'A':
			raise Exception("IMPLEMENT ARRAY REGION PACKING")
		elif c == '?':
			type_tag, rest = data[pos]
			type_tag_fmt = fmt[idx+1:idx+2]
			result.extend(pack_jdi_data(type_tag_fmt, [type_tag]))
			sub_data_fmt = get_paren_substr_after(fmt, idx+1)
			clauses = dict((int(k), v) for (k, v) in (x.split("=") for x in sub_data_fmt.split("|")))
			result.extend(pack_jdi_data(clauses[type_tag], [rest]))
			idx += 1
			pos += 1
		elif c == 'R':
			num = len(data[pos])
			result.extend(struct.pack(">I", num))
			sub_result = []
			sub_data_fmt = get_paren_substr_after(fmt, idx)
			for i in range(num):
				sub_data = pack_jdi_data(sub_data_fmt, [data[pos][i]])
				sub_result.append(sub_data)
			pos += 1
			result.extend(b"".join(sub_result))
		elif c == '(':
			in_paren = 1
		idx += 1
	return result

def get_paren_substr_after(fmt, idx):
	if fmt[idx+1] != '(':
		raise Exception("jdi_data fmt exception: expected '(' at %d of '%s'" % (idx, fmt))
	close_paren = find_close_paren(fmt, idx+1)
	if close_paren == -1:
		raise Exception("jdi_data fmt exception: no matching ')' for paren at %d of '%s'" % (idx, fmt))
	return fmt[idx+2:close_paren]

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

def read_all(sock, num_bytes):
	msgparts = []
	remaining = num_bytes
	while remaining > 0:
		chunk = sock.recv(remaining)
		msgparts.append(chunk)
		remaining -= len(chunk)
	return b''.join(msgparts)
