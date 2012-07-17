#!/usr/bin/python

import fnmatch
import time
import os
from jdwp import jdwp
from jdwp_constants import *

def main():

	sourceroots = ["src/java"]

	known_sourcefiles = dict()
	for sourceroot in sourceroots:
		for root, dirnames, filenames in os.walk(sourceroot):
			for filename in fnmatch.filter(filenames, '*.java'):
				known_sourcefiles[filename] = os.path.join(root, filename)

	jdwp_lib = jdwp()

  # make sure things are running
	jdwp_lib.vm_resume()

	# load classes and invert resulting rows into a dict with classid as key
	#all_classes = dict((v[1], v) for v in jdwp_lib.get_reply(jdwp_lib.vm_all_classes())[0])

	#all_sourcefiles = dict((c,jdwp_lib.rt_source_file_sync([c])) for c in all_classes)
	#print(all_sourcefiles)

	#sourcefiles = dict(
	#		(k, all_sourcefiles[k][0]) for k in all_sourcefiles if
	#				all_sourcefiles[k] != [] and all_sourcefiles[k][0] in known_sourcefiles)

	#source_classes = [k for k in sourcefiles]

	#source_methods = [(source_class, jdwp_lib.rt_methods_sync([source_class])[0]) for source_class in source_classes]

	#source_index = dict()
	#for sm in source_methods:
	#	for m in sm[1]:
	#		cid = sm[0]
	#		mid = m[0]
	#		filename = known_sourcefiles[sourcefiles[cid]]
	#		line_table = jdwp_lib.m_line_table_sync([cid, mid])[2]
	#		for index, sourceline in line_table:
	#			source_index[(filename, sourceline)] = (all_classes[cid][0], cid, mid, index)

	#location = source_index[("src/java/testprog.java", 32)]

	#print(location)

	#event_kind = EVENT_KIND_BREAKPOINT
	#suspend_policy = SUSPEND_POLICY_ALL
	#modifiers = [(7, location)]

	#event_request = [
	#		event_kind,
	#		suspend_policy,
	#		modifiers]

	#breakpoint_id = jdwp_lib.er_set_sync(event_request)[0]
	#print(breakpoint_id)

	#threads = jdwp_lib.vm_all_threads_sync()[0]
	#for thread in threads:
	#	thread_name = jdwp_lib.tr_name_sync(thread)[0]
	#	if thread_name == 'main':
	#		thread_id = thread[0]
	#		break

	#events = [(2, (breakpoint_id, thread_id, location[0], location[1], location[2], location[3]))]
	#composite_request = [
	#		suspend_policy,
	#		events]

	#print(jdwp_lib.e_composite_sync(composite_request))

	#while True:
	#	print("waiting")
	#	print(jdwp_lib.pop_reply(req_id))

if __name__ == '__main__':
	main()
