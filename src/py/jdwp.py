import socket
import struct
import sys
import traceback
from jdwp_constants import *
from jdwp_util import *

cmd_specs = dict()

# vm command set (1)
cmd_specs["vm_version"] = (VM_CMDSET, VM_CMD_VERSION, "", "SIISS")
cmd_specs["vm_classes_by_signature"] = (VM_CMDSET, VM_CMD_CLASSES_BY_SIGNATURE, "S", "R(BLI)")
cmd_specs["vm_all_classes"] = (VM_CMDSET, VM_CMD_ALL_CLASSES, "", "R(BLSI)")
cmd_specs["vm_all_threads"] = (VM_CMDSET, VM_CMD_ALL_THREADS, "", "R(L)")
cmd_specs["vm_top_level_thread_groups"] = (VM_CMDSET, VM_CMD_TOP_LEVEL_THREAD_GROUPS, "", "R(L)")
cmd_specs["vm_dispose"] = (VM_CMDSET, VM_CMD_DISPOSE, "", "")
cmd_specs["vm_id_sizes"] = (VM_CMDSET, VM_CMD_ID_SIZES, "", "IIIII")
cmd_specs["vm_suspend"] = (VM_CMDSET, VM_CMD_SUSPEND, "", "")
cmd_specs["vm_resume"] = (VM_CMDSET, VM_CMD_RESUME, "", "")
cmd_specs["vm_create_string"] = (VM_CMDSET, VM_CMD_CREATE_STRING, "", "L")
cmd_specs["vm_capabilities"] = (VM_CMDSET, VM_CMD_CAPABILITIES, "", "bbbbbbb")
cmd_specs["vm_classpaths"] = (VM_CMDSET, VM_CMD_CLASSPATHS, "", "SR(S)R(S)")
cmd_specs["vm_capabilities_new"] = (VM_CMDSET, VM_CMD_CAPABILITIES_NEW, "", "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")

# reference type command set (2)
cmd_specs["rt_signature"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_SIGNATURE, "L", "S")
cmd_specs["rt_class_loader"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_CLASS_LOADER, "L", "L")
cmd_specs["rt_modifiers"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_MODIFIERS, "L", "I")
cmd_specs["rt_fields"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_FIELDS, "L", "R(LSSI)")
cmd_specs["rt_methods"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_METHODS, "L", "R(LSSI)")
cmd_specs["rt_get_values"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_GET_VALUES, "LR(L)", "R(V)")
cmd_specs["rt_source_file"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_SOURCE_FILE, "L", "S")
cmd_specs["rt_nested_types"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_NESTED_TYPES, "L", "R(BL)")
cmd_specs["rt_status"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_STATUS, "L", "I")
cmd_specs["rt_interfaces"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_INTERFACES, "L", "R(L)")
cmd_specs["rt_class_object"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_CLASS_OBJECT, "L", "L")
cmd_specs["rt_source_debug_extension"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_SOURCE_DEBUG_EXTENSION, "L", "S")
cmd_specs["rt_signature_with_generic"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_SIGNATURE_WITH_GENERIC, "L", "SS")
cmd_specs["rt_fields_with_generic"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_FIELDS_WITH_GENERIC, "L", "R(LSSSI)")
cmd_specs["rt_methods_with_generic"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_METHODS_WITH_GENERIC, "L", "R(LSSSI)")
cmd_specs["rt_instances"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_METHODS_WITH_GENERIC, "LI", "R(T)")
cmd_specs["rt_class_file_version"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_CLASS_FILE_VERSION, "L", "II")
cmd_specs["rt_constant_pool"] = (REF_TYPE_CMDSET, REF_TYPE_CMD_CONSTANT_POOL, "L", "IR(B)")

# class type command set (3)
cmd_specs["ct_superclass"] = (CLASS_TYPE_CMDSET, CLASS_TYPE_CMD_SUPERCLASS, "L", "L")
cmd_specs["ct_set_values"] = (CLASS_TYPE_CMDSET, CLASS_TYPE_CMD_SET_VALUES, "LR(LV)", "")
cmd_specs["ct_invoke_method"] = (CLASS_TYPE_CMDSET, CLASS_TYPE_CMD_INVOKE_METHOD, "LLLR(V)I", "VT")
cmd_specs["ct_new_instance"] = (CLASS_TYPE_CMDSET, CLASS_TYPE_CMD_NEW_INSTANCE, "LLLR(V)I", "TT")

# array type command set (4)
cmd_specs["at_new_instance"] = (ARRAY_TYPE_CMDSET, ARRAY_TYPE_CMD_NEW_INSTANCE, "LI", "T")

# interface command set (5)
# ...is empty

# method command set (6)
cmd_specs["m_line_table"] = (METHOD_CMDSET, METHOD_CMD_LINE_TABLE, "LL", "LLR(LI)")
cmd_specs["m_variable_table"] = (METHOD_CMDSET, METHOD_CMD_VARIABLE_TABLE, "LL", "IR(LSSII)")
cmd_specs["m_bytecodes"] = (METHOD_CMDSET, METHOD_CMD_BYTECODES, "LL", "R(B)")
cmd_specs["m_is_obsolete"] = (METHOD_CMDSET, METHOD_CMD_IS_OBSOLETE, "LL", "b")
cmd_specs["m_variable_table_with_generic"] = (METHOD_CMDSET, METHOD_CMD_VARIABLE_TABLE_WITH_GENERIC, "LL", "IR(LSSSII)")

# non-existent command set (7)
# ...doesn't exist

# field command set (8)
# ...is empty

# object reference command set (9)
cmd_specs["or_reference_type"] = (OBJ_REF_CMDSET, OBJ_REF_CMD_REFERENCE_TYPE, "L", "BL")
cmd_specs["or_get_values"] = (OBJ_REF_CMDSET, OBJ_REF_CMD_GET_VALUES, "LR(L)", "R(V)")
cmd_specs["or_set_values"] = (OBJ_REF_CMDSET, OBJ_REF_CMD_SET_VALUES, "LR(LV)", "")
cmd_specs["or_monitor_info"] = (OBJ_REF_CMDSET, OBJ_REF_CMD_MONITOR_INFO, "L", "LIIR(L)")
cmd_specs["or_invoke_method"] = (OBJ_REF_CMDSET, OBJ_REF_CMD_INVOKE_METHOD, "LLLLR(V)I", "VT")
cmd_specs["or_disable_collection"] = (OBJ_REF_CMDSET, OBJ_REF_CMD_DISABLE_COLLECTION, "L", "")
cmd_specs["or_enable_collection"] = (OBJ_REF_CMDSET, OBJ_REF_CMD_ENABLE_COLLECTION, "L", "")
cmd_specs["or_is_collected"] = (OBJ_REF_CMDSET, OBJ_REF_CMD_IS_COLLECTED, "L", "b")
cmd_specs["or_referring_objects"] = (OBJ_REF_CMDSET, OBJ_REF_CMD_REFERRING_OBJECTS, "LI", "R(T)")

# string reference command set (10)
cmd_specs["sr_value"] = (STR_REF_CMDSET, STR_REF_CMD_VALUE, "L", "S")

# thread reference command set (11)
cmd_specs["tr_name"] = (THREAD_REF_CMDSET, THREAD_REF_CMD_NAME, "L", "S")
cmd_specs["tr_suspend"] = (THREAD_REF_CMDSET, THREAD_REF_CMD_SUSPEND, "L", "")
cmd_specs["tr_resume"] = (THREAD_REF_CMDSET, THREAD_REF_CMD_RESUME, "L", "")
cmd_specs["tr_status"] = (THREAD_REF_CMDSET, THREAD_REF_CMD_STATUS, "L", "II")
cmd_specs["tr_thread_group"] = (THREAD_REF_CMDSET, THREAD_REF_CMD_THREAD_GROUP, "L", "L")
cmd_specs["tr_frames"] = (THREAD_REF_CMDSET, THREAD_REF_CMD_FRAMES, "LII", "R(LX)")
cmd_specs["tr_frame_count"] = (THREAD_REF_CMDSET, THREAD_REF_CMD_FRAME_COUNT, "L", "I")
cmd_specs["tr_owned_monitors"] = (THREAD_REF_CMDSET, THREAD_REF_CMD_OWNED_MONITORS, "L", "R(T)")
cmd_specs["tr_current_contended_monitor"] = (THREAD_REF_CMDSET, THREAD_REF_CMD_CURRENT_CONTENDED_MONITOR, "L", "T")
cmd_specs["tr_stop"] = (THREAD_REF_CMDSET, THREAD_REF_CMD_STOP, "LL", "")
cmd_specs["tr_interrupt"] = (THREAD_REF_CMDSET, THREAD_REF_CMD_INTERRUPT, "L", "")
cmd_specs["tr_suspend_count"] = (THREAD_REF_CMDSET, THREAD_REF_CMD_INTERRUPT, "L", "I")
cmd_specs["tr_owned_monitors_stack_depth_info"] = (THREAD_REF_CMDSET, THREAD_REF_CMD_OWNED_MONITORS_STACK_DEPTH_INFO, "L", "R(TI)")
cmd_specs["tr_force_early_return"] = (THREAD_REF_CMDSET, THREAD_REF_CMD_FORCE_EARLY_RETURN, "LV", "")

# thread group reference command set (12)
cmd_specs["tgr_name"] = (THREAD_GRP_REF_CMDSET, THREAD_GRP_REF_CMD_NAME, "L", "S")
cmd_specs["tgr_parent"] = (THREAD_GRP_REF_CMDSET, THREAD_GRP_REF_CMD_PARENT, "L", "L")
cmd_specs["tgr_children"] = (THREAD_GRP_REF_CMDSET, THREAD_GRP_REF_CMD_CHILDREN, "L", "R(L)R(L)")

# array reference command set (13)
cmd_specs["ar_length"] = (ARRAY_REF_CMDSET, ARRAY_REF_CMD_LENGTH, "L", "I")
cmd_specs["ar_get_values"] = (ARRAY_REF_CMDSET, ARRAY_REF_CMD_GET_VALUES, "LII", "A")
cmd_specs["ar_set_values"] = (ARRAY_REF_CMDSET, ARRAY_REF_CMD_SET_VALUES, "LIR(V)", "")

# class loader reference command set (14)
cmd_specs["clr_visible_classes"] = (CLASS_LOADER_REF_CMDSET, CLASS_LOADER_REF_CMD_VISIBLE_CLASSES, "L", "R(BL)")

# event request command set (15)
cmd_specs["er_set"] = (EVENT_REQ_CMDSET, EVENT_REQ_CMD_SET, "BBR(?B(1=I|2=I|3=L|4=L|5=S|6=S|7=X|8=Lbb|9=LL|10=LII|11=L|12=S))", "I")
cmd_specs["er_clear"] = (EVENT_REQ_CMDSET, EVENT_REQ_CMD_CLEAR, "BI", "")
cmd_specs["er_clear_all_breakpoints"] = (EVENT_REQ_CMDSET, EVENT_REQ_CMD_CLEAR_ALL_BREAKPOINTS, "", "")

# stack frame command set (16)
cmd_specs["sf_get_values"] = (STACK_FRAME_CMDSET, STACK_FRAME_CMD_GET_VALUES, "LLR(IB)", "R(V)")
cmd_specs["sf_set_values"] = (STACK_FRAME_CMDSET, STACK_FRAME_CMD_SET_VALUES, "LLR(IV)", "")
cmd_specs["sf_this_object"] = (STACK_FRAME_CMDSET, STACK_FRAME_CMD_THIS_OBJECT, "LL", "T")
cmd_specs["sf_pop_frames"] = (STACK_FRAME_CMDSET, STACK_FRAME_CMD_POP_FRAMES, "LL", "")

# class object reference command set (17)
cmd_specs["cor_reflected_type"] = (CLASS_OBJ_REF_CMDSET, CLASS_OBJ_REF_CMD_REFLECTED_TYPE, "L", "BL")

# event command set (64)
cmd_specs["e_composite"] = (EVENT_CMDSET, EVENT_CMD_COMPOSITE,
		"BR(?B("
		+ str(EVENT_KIND_VM_START) + "=IL|"
		+ str(EVENT_KIND_SINGLE_STEP) + "=ILX|"
		+ str(EVENT_KIND_BREAKPOINT) + "=ILX|"
		+ str(EVENT_KIND_METHOD_ENTRY) + "=ILX|"
		+ str(EVENT_KIND_METHOD_EXIT) + "=ILX|"
		+ str(EVENT_KIND_METHOD_EXIT_WITH_RETURN_VALUE) + "=ILXV|"
		+ str(EVENT_KIND_MONITOR_CONTENDED_ENTERED) + "=ILTX|"
		+ str(EVENT_KIND_MONITOR_WAIT) + "=ILTXL|"
		+ str(EVENT_KIND_MONITOR_WAITED) + "=ILTXb|"
		+ str(EVENT_KIND_EXCEPTION) + "=ILXTX|"
		+ str(EVENT_KIND_THREAD_START) + "=IL|"
		+ str(EVENT_KIND_THREAD_DEATH) + "=IL|"
		+ str(EVENT_KIND_CLASS_PREPARE) + "=ILBLSI|"
		+ str(EVENT_KIND_CLASS_UNLOAD) + "=IS|"
		+ str(EVENT_KIND_FIELD_ACCESS) + "=ILXBLLT|"
		+ str(EVENT_KIND_FIELD_MODIFICATION) + "=ILXBLLTV|"
		+ str(EVENT_KIND_VM_DEATH) + "=I))")



class jdwp:

	def __init__(self, port = 5005):

		parse_jdwp_spec("/home/cgs/code/debug/tmp/openjdk/jdk/make/jpda/jdwp/jdwp.spec")
		self.generate_methods()

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

	def generate_methods(self):
		for key in cmd_specs:
			cmdset = cmd_specs[key][0]
			cmd = cmd_specs[key][1]
			packing_str = cmd_specs[key][2]
			setattr(self.__class__, key, self.func_creator(key, cmdset, cmd, packing_str))
			setattr(self.__class__, key + "_sync", self.func_creator(key, cmdset, cmd, packing_str, True))

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
