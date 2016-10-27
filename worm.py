# Imports
import socket, struct
import subprocess

# Functions
def get_default_gateway_linux():
    """Read the default gateway directly from /proc."""
    with open("/proc/net/route") as fh:
        for line in fh:
            fields = line.strip().split()
            if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                continue

            return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))

# Find info about self
my_ip = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
print (my_ip)
x = my_ip.split(".")
my_octet = x[3] if len(x) > 3 else 0

print(my_octet)

gateway = get_default_gateway_linux()
x = gateway.split(".")
gateway_octet = x[3] if len(x) > 3 else 0

print(gateway_octet)

# Find targets (all ips in a /24 scope)
targets = list(range(1, 254))

# Remove self and default gateway from targets
targets.remove(int(gateway_octet))
targets.remove(int(my_octet))

# Wait for previous to respond, if previous is given


# Transfer to target


# Halt and catch fire