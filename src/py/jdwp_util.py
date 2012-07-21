import struct
import re

from pyparsing import *

def parse_jdwp_spec(specfile, command_set_handler, constant_set_handler):
	print("START")

	f = open(specfile, 'r')
	spec = f.read()
	f.close()

	grammar = spec_file_grammar(command_set_handler, constant_set_handler)

	try:
		return grammar.parseString(spec)
	except ParseException as e:
		print(e)


def spec_file_grammar(command_set_handler, constant_set_handler):
	identifier = Regex(r'[a-zA-Z][a-zA-Z0-9_-]*')
	decimal = Regex(r'[0-9]+\b')
	hexadecimal = Regex("0x[0-9a-f]+")
	open_paren = Literal("(").suppress()
	open_select_spec = open_paren + Keyword("Select")
	open_event_packet = open_paren + Keyword("Event")
	open_alt_spec = open_paren + Keyword("Alt")
	open_out_packet = open_paren + Keyword("Out")
	open_reply_packet = open_paren + Keyword("Reply")
	open_group_spec = open_paren + Keyword("Group")
	open_repeat_spec = open_paren + Keyword("Repeat")
	open_error_spec = open_paren + Keyword("Error")
	open_error_set = open_paren + Keyword("ErrorSet")
	string = OneOrMore(QuotedString('"', '\\')).suppress()
	equal_sign = Literal("=").suppress()
	constant_reference = Regex("[a-zA-Z0-9_.]+")
	rhs = decimal | hexadecimal | sglQuotedString | constant_reference
	open_command = open_paren + Keyword("Command").suppress()
	close_paren = Literal(")").suppress()
	open_constant =  open_paren + Keyword("Constant" ).suppress()
	open_command_set =  open_paren + Keyword("CommandSet" ).suppress()
	open_constant_set =  open_paren + Keyword("ConstantSet" ).suppress()

	argument_spec = Forward()
	assignment = identifier + equal_sign + rhs

	alt_spec = open_alt_spec + assignment + Optional(string) + OneOrMore(argument_spec) + close_paren
	group_spec = open_group_spec + identifier + Optional(string) + OneOrMore(argument_spec) + close_paren
	type_spec = open_paren + identifier + identifier + Optional(string) + close_paren
	select_spec = open_select_spec + identifier + type_spec + (OneOrMore(alt_spec)) + close_paren
	repeat_spec = open_repeat_spec + identifier + Optional(string) + (type_spec | group_spec | select_spec) + close_paren
	argument_spec << (type_spec | repeat_spec | select_spec)

	error_spec = open_error_spec + Regex(r'[A-Z_]+') + Optional(string) + close_paren
	out_packet = open_out_packet + argument_spec*(None,None) + Optional(string) + close_paren
	reply_packet = open_reply_packet + argument_spec*(None,None) + Optional(string) + close_paren
	error_set = open_error_set + error_spec*(None,None) + close_paren
	command = open_command + assignment + Optional(string) + out_packet + reply_packet + error_set + close_paren
	constant = open_constant + assignment + Optional(string) + close_paren

	# composite is weird. i dunno...
	event_packet = open_event_packet + Optional(string) + type_spec + repeat_spec + close_paren
	composite = open_command + assignment + Optional(string) + event_packet + close_paren

	command_set = open_command_set + assignment + ZeroOrMore(Group(command|composite)) + close_paren
	command_set.setParseAction(command_set_handler)
	constant_set = open_constant_set + identifier + Optional(string) + OneOrMore(Group(constant)) + close_paren
	constant_set.setParseAction(constant_set_handler)
	result = cStyleComment + "JDWP" + string + command_set*(1,None) + constant_set*(1,None)
	result.setDefaultWhitespaceChars(' \t\n')
	return result

def get_paren_substr_after(fmt, idx):
	if fmt[idx+1] != '(':
		raise Exception("jdi_data fmt exception: expected '(' at %d of '%s'" % (idx, fmt))
	close_paren = find_close_paren(fmt, idx+1)
	if close_paren == -1:
		raise Exception("jdi_data fmt exception: no matching ')' for paren at %d of '%s'" % (idx, fmt))
	return fmt[idx+2:close_paren]

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
