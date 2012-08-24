#!/usr/bin/python
# coding: utf-8
import json
import os
import requests
import re
import sys
from style import header,warn,fail,bold,blue,green

REQUEST_METHOD = 'request-method';
GET = 'get'
POST = 'post'
REQUEST_DATA = 'request-data'
TEST_FILE_EXTENSION = '.test'
REQUEST_URL = 'request-url'
EXPECTED_RESPONSE = 'response'
TEST_NAME = 'name'
IGNORE_WHITESPACE = 'ignore-whitespace'
AUTHOR = 'author'
DEFAULT_MESSAGE_FILLER = '####'
MESSAGE_FILLER = 'message-filler'
GLOBAL_STORE = 'global-test-data-store'

test_count = 0
test_not_executed = 0
test_passed = 0
test_failed = 0
test_data = []

def getter(field_name,default):
	return lambda test_index,test_data: test_data[test_index][field_name] if (test_data[test_index].has_key(field_name)) else (test_data[0][field_name] if (test_data[0].has_key(field_name)) else default)

get_request_data = getter(REQUEST_DATA,{})
get_author_name = getter(AUTHOR,'')
get_request_method = getter(REQUEST_METHOD,GET)
get_message_filler = getter(MESSAGE_FILLER,DEFAULT_MESSAGE_FILLER)
get_ignore_whitespace = getter(IGNORE_WHITESPACE,False)
get_expected_response = getter(EXPECTED_RESPONSE,'')
get_request_url = getter(REQUEST_URL,None)

def min_required_data_present_in(index,data):
	request_url = get_request_url(index,data)
	expected_response = get_expected_response(index,data)
	if(request_url is not None  and expected_response != ''):
		return True
	return False

def clean_whitespace(input):
	return re.sub('\s+','',input)

def response_match(actual,expected,message_filler):
	global test_data
	parts = expected.split(message_filler)
	match = True
	index = 0;
	firstpart = True
	for part in parts:
		match_len = actual[index:].find(part)
		if(match_len == -1):
			match=False
			break
		elif(not firstpart):
			test_data[0][GLOBAL_STORE].append(actual[index:index+match_len].strip())
		firstpart = False

		index += match_len+len(part)
	return match

def replace_with_global_data(input):
	global test_data
	for i in range(1,len(test_data[0][GLOBAL_STORE])+1):
		token = '\{\$'+str(i)+'\}'
		input = re.sub(token,test_data[0][GLOBAL_STORE][i-1],input)
	return input

def is_list_of_dicts(data):
	result = True;
	if(type(data) != list):
		result = False
	if(result and len(data) < 2): # data[0] = config, data[1] = test
		result = False
	if(result):
		for data_element in data:
			if(type(data_element) != dict):
				result = False
				break;
	return result;


def get_test_name(test_index,test_data,file_name):
	if(test_data[test_index].has_key(TEST_NAME)):
		return test_data[test_index][TEST_NAME]
	if(test_data[0].has_key(TEST_NAME)):
		return test_data[0][TEST_NAME]
	return file_name[: -1 * len(TEST_FILE_EXTENSION)]

def check_test_result(test_name, test_index, response, test_data):
	global test_passed, test_failed
	if response is None:
		print blue(test_name+" ("+str(test_index)+")") + fail(": Test failed ") + ("" if len(author) == 0 else blue(" contact test author: "+author+""))
		print "response is None"
		test_failed += 1
		return

	if response.status_code != 200:
		print blue(test_name+" ("+str(test_index)+")") + fail(": Test failed ") + ("" if len(author) == 0 else blue(" contact test author: "+author+""))
		print "HTTP status code = "+response.status_code
		test_failed += 1
		return

	message_filler = get_message_filler(test_index,test_data)
	ignore_whitespace = get_ignore_whitespace(test_index,test_data)
	expected_response = replace_with_global_data(get_expected_response(test_index,test_data))

	if((not ignore_whitespace and response_match(response.text.strip(),expected_response, message_filler)) or ( ignore_whitespace and response_match(clean_whitespace(response.text) ,clean_whitespace(expected_response),message_filler))):
		print blue(test_name+" ("+str(test_index)+")") + green(": Test passed")
		test_passed += 1
	else:
		author = get_author_name(test_index,test_data)
		print blue(test_name+" ("+str(test_index)+")") + fail(": Test failed ") + ("" if len(author) == 0 else blue(" contact test author: "+author+""))
		print warn("EXPECTED")+": \n"+ expected_response + "\n\n"+warn("ACTUAL")+":\n" + response.text
		test_failed += 1


########## START EXECUTION ##################

#Get files
argument = './' if (len(sys.argv) != 2) else sys.argv[1]
if argument.endswith(TEST_FILE_EXTENSION):
	test_file_names = [ argument ]
else:
	dir = argument
	if(not dir.endswith('/')):
		dir = dir+'/'
	test_file_names = filter ( lambda x : x.endswith(TEST_FILE_EXTENSION), os.listdir(dir))
	test_file_names = map( lambda x : dir+x , test_file_names)

#Start executing test/s in each file
test_file_names.sort()

print header(u'Running Community API Tester!')

for test_file_name in test_file_names:
	test_file = open(test_file_name,'r')
	test_data = json.load(test_file)

	if(not is_list_of_dicts(test_data)):
		print blue(test_file_name) + warn(": Invalid file format")
		test_not_executed += 1
		continue

	if(not test_data[0].has_key(GLOBAL_STORE)):
		test_data[0][GLOBAL_STORE] = []
	test_count += (len(test_data) - 1); #first element is list is configuration and not a test

	for test_index in range(1,len(test_data)):
		if(not min_required_data_present_in(test_index,test_data)):
			print blue(test_name) + warn(": Insuffecient data to run test")
			test_not_executed += 1
			continue

		test_name = replace_with_global_data(get_test_name(test_index,test_data,test_file_name))

		request_data = get_request_data(test_index,test_data)
		for request_key, request_value in request_data.iteritems():
			request_data[request_key]=replace_with_global_data(request_data[request_key])

		request_method = get_request_method(test_index,test_data)
		request_url = get_request_url(test_index,test_data)
        	
		response = None 
		try:
			if(request_method.lower() == POST):
				response = requests.post(request_url,data=request_data)
			else:
				response = requests.get(request_url,params=request_data)
		except:
			pass

		check_test_result(test_name,test_index,response,test_data)

print header("Results:")
print blue("Total tests: ") + bold(str(test_count)) + blue(", Tests passed : ") + bold(str(test_passed)) + blue(", Tests failed : ") + bold(str(test_failed))+ blue(", Tests not executed : ") + bold(str(test_not_executed))

