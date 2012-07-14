#!/usr/bin/python

import sys
import socket
import struct

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
      result.append(struct.unpack(str(strlen) + "s", data[pos+4:pos+strlen+4])[0])
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

def pack_jdi_data(fmt, data):
  print("fmt %s   data %s" % (fmt, data))
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
    if c == 'S':
      strlen = len(data[pos])
      result.extend(struct.pack(">I", strlen))
      result.extend(bytearray(data[pos], 'UTF-8'))
      pos += 1
    elif c == 'I':
      result.extend(struct.pack(">I", data[pos]))
      pos += 1
    elif c == 'b':
      result.extend(struct.pack(">B", data[pos]))
      pos += 1
    elif c == 'B':
      result.extend(struct.pack(">B", data[pos]))
      pos += 1
    elif c == 'L':
      result.extend(struct.pack(">Q", data[pos]))
      pos += 1
    elif c == 'R':
      num = len(data[pos])
      result.extend(struct.pack(">I", num))
      sub_result = []
      if fmt[idx+1] != '(':
        raise Exception("jdi_data fmt exception: expect '(' after 'R'")
      close_paren = find_close_paren(fmt, idx+1)
      if close_paren == -1:
        raise Exception("jdi_data fmt exception: no matching ')'")
      sub_data_fmt = fmt[idx+2:close_paren]
      for i in range(num):
        print(sub_data_fmt)
        sub_data = pack_jdi_data(sub_data_fmt, [data[pos][i],])
        sub_result.append(sub_data)
        print("sub_data: %s   sub_result: %s" % (sub_data, sub_result))
      pos += 1
      result.extend(b"".join(sub_result))
    elif c == '(':
      in_paren = 1
    idx += 1
  return result

tag_constants_data_sizes = dict()
TAG_CONSTANT_ARRAY = 91
TAG_CONSTANT_BYTE = 66
TAG_CONSTANT_CHAR = 67
TAG_CONSTANT_OBJECT = 76
TAG_CONSTANT_FLOAT = 70
TAG_CONSTANT_DOUBLE = 68
TAG_CONSTANT_INT = 73
TAG_CONSTANT_LONG = 74
TAG_CONSTANT_SHORT = 83
TAG_CONSTANT_VOID = 86
TAG_CONSTANT_BOOLEAN = 90
TAG_CONSTANT_STRING = 115
TAG_CONSTANT_THREAD = 116
TAG_CONSTANT_THREAD_GROUP = 103
TAG_CONSTANT_CLASS_LOADER = 108
TAG_CONSTANT_CLASS_OBJECT = 99
tag_constants_data_sizes[TAG_CONSTANT_ARRAY] = 8
tag_constants_data_sizes[TAG_CONSTANT_BYTE] = 1
tag_constants_data_sizes[TAG_CONSTANT_CHAR] = 2
tag_constants_data_sizes[TAG_CONSTANT_OBJECT] = 8
tag_constants_data_sizes[TAG_CONSTANT_FLOAT] = 4
tag_constants_data_sizes[TAG_CONSTANT_DOUBLE] = 8
tag_constants_data_sizes[TAG_CONSTANT_INT] = 4
tag_constants_data_sizes[TAG_CONSTANT_LONG] = 8
tag_constants_data_sizes[TAG_CONSTANT_SHORT] = 2
tag_constants_data_sizes[TAG_CONSTANT_VOID] = 0
tag_constants_data_sizes[TAG_CONSTANT_BOOLEAN] = 8
tag_constants_data_sizes[TAG_CONSTANT_STRING] = 8
tag_constants_data_sizes[TAG_CONSTANT_THREAD] = 8
tag_constants_data_sizes[TAG_CONSTANT_THREAD_GROUP] = 8
tag_constants_data_sizes[TAG_CONSTANT_CLASS_LOADER] = 8
tag_constants_data_sizes[TAG_CONSTANT_CLASS_OBJECT] = 8

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

VM_CMD_SET                      =  1
VM_CMD_VERSION                  =  1
VM_CMD_CLASSES_BY_SIGNATURE     =  2
VM_CMD_ALL_CLASSES              =  3
VM_CMD_ALL_THREADS              =  4
VM_CMD_TOP_LEVEL_THREAD_GROUPS  =  5
VM_CMD_DISPOSE                  =  6
VM_CMD_ID_SIZES                 =  7
VM_CMD_SUSPEND                  =  8
VM_CMD_RESUME                   =  9
VM_CMD_EXIT                     = 10
VM_CMD_CREATE_STRING            = 11
VM_CMD_CAPABILITIES             = 12
VM_CMD_CLASSPATHS               = 13
VM_CMD_DISPOSE_OBJECTS          = 14
VM_CMD_HOLD_EVENTS              = 15
VM_CMD_RELEASE_EVENTS           = 16
VM_CMD_CAPABILITIES_NEW         = 17
VM_CMD_REDEFINE_CLASSES         = 18
VM_CMD_SET_DEFAULT_STRATUM      = 19

REF_TYPE_CMD_SET                =  2
REF_TYPE_CMD_SIGNATURE          =  1
REF_TYPE_CMD_CLASS_LOADER       =  2
REF_TYPE_CMD_MODIFIERS          =  3
REF_TYPE_CMD_FIELDS             =  4
REF_TYPE_CMD_METHODS            =  5
REF_TYPE_CMD_GET_VALUES         =  6

parsers = dict()
parsers[(VM_CMD_SET, VM_CMD_VERSION)] = lambda data : unpack_jdi_data("SIISS", data)
parsers[(VM_CMD_SET, VM_CMD_CLASSES_BY_SIGNATURE)] = lambda data : unpack_jdi_data("R(BLI)", data)
parsers[(VM_CMD_SET, VM_CMD_ALL_CLASSES)] = lambda data : unpack_jdi_data("R(BLSI)", data)
parsers[(VM_CMD_SET, VM_CMD_ALL_THREADS)] = lambda data : unpack_jdi_data("R(L)", data)
parsers[(VM_CMD_SET, VM_CMD_TOP_LEVEL_THREAD_GROUPS)] = lambda data : unpack_jdi_data("R(L)", data)
parsers[(VM_CMD_SET, VM_CMD_ID_SIZES)] = lambda data : unpack_jdi_data("IIIII", data)
parsers[(VM_CMD_SET, VM_CMD_CREATE_STRING)] = lambda data : unpack_jdi_data("L", data)
parsers[(VM_CMD_SET, VM_CMD_CAPABILITIES)] = lambda data : unpack_jdi_data("bbbbbbb", data)
parsers[(VM_CMD_SET, VM_CMD_CLASSPATHS)] = lambda data : unpack_jdi_data("SR(S)R(S)", data)
parsers[(VM_CMD_SET, VM_CMD_CAPABILITIES_NEW)] = lambda data : unpack_jdi_data("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", data)
parsers[(REF_TYPE_CMD_SET, REF_TYPE_CMD_SIGNATURE)] = lambda data : unpack_jdi_data("S", data)
parsers[(REF_TYPE_CMD_SET, REF_TYPE_CMD_CLASS_LOADER)] = lambda data : unpack_jdi_data("L", data)
parsers[(REF_TYPE_CMD_SET, REF_TYPE_CMD_MODIFIERS)] = lambda data : unpack_jdi_data("I", data)
parsers[(REF_TYPE_CMD_SET, REF_TYPE_CMD_FIELDS)] = lambda data : unpack_jdi_data("R(LSSI)", data)
parsers[(REF_TYPE_CMD_SET, REF_TYPE_CMD_METHODS)] = lambda data : unpack_jdi_data("R(LSSI)", data)
parsers[(REF_TYPE_CMD_SET, REF_TYPE_CMD_GET_VALUES)] = lambda data : unpack_jdi_data("R(V)", data)

class debugger:

  def __init__(self, port = 5005):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.connect(('localhost', port))

    # handshake
    self.sock.send(bytes('JDWP-Handshake', 'UTF-8'))
    data = self.sock.recv(14)
    if data != b'JDWP-Handshake':
      raise Exception('Failed handshake')

    # dict of req_id -> (cmd_set, cmd)
    self.requests = dict()
    # dict of req_id -> reply
    self.replies = dict()

    self.next_req_id = 0
    
    req_id = self.vm_version()
    self.version_info = self.get_reply(req_id)

    req_id = self.vm_id_sizes()
    self.id_size_info = self.get_reply(req_id)

# BEGIN JDI METHOD DEFINITONS

  def vm_version(self):
    return self.async_command(VM_CMD_SET, VM_CMD_VERSION)

  def vm_classes_by_signature(self, signature):
    return self.async_command(VM_CMD_SET, VM_CMD_CLASSES_BY_SIGNATURE, self.encode_string(signature))

  def vm_all_classes(self):
    return self.async_command(VM_CMD_SET, VM_CMD_ALL_CLASSES)

  def vm_all_threads(self):
    return self.async_command(VM_CMD_SET, VM_CMD_ALL_THREADS)

  def vm_top_level_thread_groups(self):
    return self.async_command(VM_CMD_SET, VM_CMD_TOP_LEVEL_THREAD_GROUPS)

  def vm_dispose(self):
    return self.async_command(VM_CMD_SET, VM_CMD_DISPOSE)

  def vm_id_sizes(self):
    return self.async_command(VM_CMD_SET, VM_CMD_ID_SIZES)

  def vm_suspend(self):
    return self.async_command(VM_CMD_SET, VM_CMD_SUSPEND)

  def vm_resume(self):
    return self.async_command(VM_CMD_SET, VM_CMD_RESUME)

  def vm_exit(self, code):
    return self.async_command(VM_CMD_SET, VM_CMD_EXIT, struct.pack(">I", code))

  def vm_create_string(self, string):
    return self.async_command(VM_CMD_SET, VM_CMD_CREATE_STRING, self.encode_string(string))

  def vm_capabilities(self):
    return self.async_command(VM_CMD_SET, VM_CMD_CAPABILITIES)

  def vm_classpaths(self):
    return self.async_command(VM_CMD_SET, VM_CMD_CLASSPATHS)

  def vm_dispose_objects(self, objects):
    raise Exception("Unsupported operation: dispose_objects hasn't been implemented yet")

  def vm_hold_events(self):
    return self.async_command(VM_CMD_SET, VM_CMD_HOLD_EVENTS)

  def vm_release_events(self):
    return self.async_command(VM_CMD_SET, VM_CMD_RELEASE_EVENTS)

  def vm_redefine_classes(self, classes):
    raise Exception("Unsupported operation: redefine_classes hasn't been implemented yet")

  def vm_set_default_stratum(self, stratum):
    return self.async_command(VM_CMD_SET, VM_CMD_SET_DEFAULT_STRATUM,
        self.encode_string(stratum))

  def rt_signature(self, rtid):
    return self.async_command(REF_TYPE_CMD_SET, REF_TYPE_CMD_SIGNATURE,
        struct.pack(">Q", rtid))

  def rt_class_loader(self, rtid):
    return self.async_command(REF_TYPE_CMD_SET, REF_TYPE_CMD_CLASS_LOADER,
        struct.pack(">Q", rtid))

  def rt_modifiers(self, rtid):
    return self.async_command(REF_TYPE_CMD_SET, REF_TYPE_CMD_MODIFIERS,
        struct.pack(">Q", rtid))

  def rt_fields(self, rtid):
    return self.async_command(REF_TYPE_CMD_SET, REF_TYPE_CMD_FIELDS,
        struct.pack(">Q", rtid))

  def rt_methods(self, rtid):
    return self.async_command(REF_TYPE_CMD_SET, REF_TYPE_CMD_METHODS,
        struct.pack(">Q", rtid))

  def rt_get_values(self, rtid, fields):
    return self.async_command(REF_TYPE_CMD_SET, REF_TYPE_CMD_GET_VALUES,
        pack_jdi_data("LR(L)", [rtid, fields]))

# END JDI METHOD DEFINITONS

  def encode_string(self, string):
    result = bytearray()
    result.extend(struct.pack('>I', len(string)))
    result.extend(bytearray(string, 'UTF-8'))
    return result

  def async_command(self, cmd_set, cmd, data = bytearray()):
    req_id = self.request(cmd_set, cmd, data)
    self.requests[req_id] = (cmd_set, cmd)
    return req_id

  def request(self, cmd_set, cmd, data = bytearray()):
    req_id = self.generate_id()
    self.send_header(req_id, 0, cmd_set, cmd, data)
    return req_id

  def get_reply(self, req_id):
    if req_id not in self.replies:
      while req_id not in self.replies:
        reply_id, flags, err, data = self.parse_reply()
        self.replies[reply_id] = (flags, err, data)
    if self.requests[req_id] in parsers:
      if self.replies[req_id][1] != 0:
        raise Exception("Error: " + str(self.replies[req_id][1]))
      return parsers[self.requests[req_id]](self.replies[req_id][2])[0]
    return []

  def send_header(self, id, flags, cmdset, cmd, data):
    msg = bytearray()
    length = 11 + len(data)
    msg.extend(struct.pack('>IIBBB',
      length, id, flags, cmdset, cmd))
    msg.extend(data)
    print("length: %d   msg: %s" % (length, msg))
    self.sock.send(msg)

  def parse_reply(self):
    header = self.read_all(self.sock, 11)
    length, id, flags, err = struct.unpack('>IIBH', header)
    msgparts = []
    remaining = length - 11
    data = self.read_all(self.sock, remaining)
    return id, flags, err, data

  def read_all(self, src, num_bytes):
    msgparts = []
    remaining = num_bytes
    print(remaining)
    while remaining > 0:
      chunk = src.recv(remaining)
      msgparts.append(chunk)
      remaining -= len(chunk)
    return b''.join(msgparts)


  def generate_id(self):
    self.next_req_id += 1
    return self.next_req_id

def main():

  dbgr = debugger()

  req_id = dbgr.vm_all_classes()
  rply = dbgr.get_reply(req_id)
  print(rply)

  req_id = dbgr.vm_id_sizes()
  rply = dbgr.get_reply(req_id)
  print(rply)

  req_id = dbgr.vm_classes_by_signature("Ltestprog;")
  rply = dbgr.get_reply(req_id)
  rtid = rply[0][0][1]

  req_id = dbgr.rt_fields(rtid)
  rply = dbgr.get_reply(req_id)
  fields = [x[0] for x in rply[0]]
  print(fields)

  req_id = dbgr.rt_get_values(rtid, fields)
  rply = dbgr.get_reply(req_id)
  print(rply)


if __name__ == '__main__':
  main()
