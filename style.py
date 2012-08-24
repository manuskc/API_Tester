HEADER = '\033[95m'
BOLD = '\033[1m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
END = '\033[0m'

def header(str):
	return HEADER + str + END
def bold(str):
	return BOLD + str + END
def blue(str):
	return OKBLUE + str + END
def green(str):
	return OKGREEN + str + END
def warn(str):
	return WARNING + str + END
def fail(str):
	return FAIL + str + END

