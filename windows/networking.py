## This Module
from alcustoms.windows import is_admin
from alcustoms.subclasses import pairdict
## Builtin
import ipaddress
import multiprocessing
import subprocess
import threading
import typing as t
import warnings
## Third Party
import python_hosts

""" Adapted from https://stackoverflow.com/a/36646749 """
def register_named_proxyport(*names, targetip = "127.0.0.1", targetport = 8000, proxyaddress = "127.65.43.21", proxyport = 80):
    """ Uses netsh and the Windows hosts file in order to create a name which directs to another ip and port.
    
        This function requires Administrative rights. If not available, a RuntimeError will be raised.

        names is one or more names that will be resolved to the given target. If those names are already
        registered, a ValueError is raised.
        targetip is the ip that should be redirected to. The default is "127.0.0.1" (localhost).
        targetport is the port on that ip to target. The default port is 8000.
        proxyaddress is an address that netsh should listen on. It should be an address that is not
        already being monitored. The "netstat -a -n -p TCP" console command can be used to check the
        address. Default value is "127.65.43.21". If this address is already registered, a ValueError
        will be raised.
        proxyport is "80" by default and should be kept that way for use with webbrowsers.
    """
    if not is_admin():
        raise RuntimeError("register_named_proxyport requires Administrative Rights")
    try: 1 <= int(targetport) <= 65535
    except: raise ValueError("Invalid targetport")
    try: 1 <= int(proxyport) <= 65535
    except: raise ValueError("Invalid proxyport")

    cmds = "netsh","interface","portproxy","add","v4tov4",f"listenport={proxyport}",f"listenaddress={proxyaddress}",\
    f"connectport={targetport}",f"connectaddress={targetip}"
    entry = python_hosts.HostsEntry(entry_type = "ipv4", address = proxyaddress, names=names)

    subprocess.run(cmds)

    hosts = python_hosts.Hosts()
    if hosts.exists(address == proxyaddress):
        raise ValueError("Provided proxy address is already in use")
    if hosts.exists(names = names):
        raise ValueError("Provided names are already registered")
    hosts.add([entry,])
    hosts.write()

""" Adapted from https://stackoverflow.com/a/36646749 """
def remove_named_proxyport(*names, proxyaddress = "127.65.43.21", proxyport = 80):
    """ Removes the netsh and hosts file changes made by register_named_proxyport.

        This function requires Administrative rights. If not available, a RuntimeError will be raised.

        names, proxyaddress, and proxyport should all match the arguments of the same name
        passed to register_named_proxyport.
        The defaults for proxyaddress and proxyport are the same as that function.
    """
    if not is_admin():
        raise RuntimeError("remove_named_proxyport requires Administrative Rights")

    cmds = "netsh","interface","portproxy","delete","v4tov4",f"listenport={proxyport}",f"listenaddress={proxyaddress}"
    subprocess.run(cmds)

    hosts = python_hosts.Hosts()
    for name in names:
        hosts.remove_all_matching(name=name)
    hosts.write()   

def get_netsh_portproxy(mode=None):
    """ Runs the "netsh interface portproxy show" command and returns the results.

        mode should be one of the accepted args for netsh "interface portproxy show":
            all, v4tov4, v4tov6, v6tov4, v6tov6

        Returs a list of nested dicts. Each dict has a "listen" and "connect" key
        and each of those keys have a dict containing "address" and "port" keys.
    """
    if mode is None: mode = "all"
    if mode not in ["all", "v4tov4", "v4tov6", "v6tov4", "v6tov6"]:
        raise ValueError(f"Invalid get_netsh_portproxy mode: {mode}")
    cmds = ["netsh","interface","portproxy","show",mode]
    result = subprocess.run(cmds, capture_output = True, check = True, text = True)
    output = result.stdout.split("\n")[5:]
    """ Initial Format of netsh interface portproxy show:
    [blank line]
    Listen on {mode part 1}:     Connect to {mode part 2}:
    [blank line]
    Address         Port        Address     Port
    ----------      -------     ---------   ------              <- [5:] => Truncate to this point
    [Target Content]                                            <-         Begin parsing here
    """
    output = [line.split() for line in output if line.strip()]
    output = [{"listen":{"address":line[0],"port":line[1]}, "connect":{"address":line[2],"port":line[3]} } for line in output]
    return output


def named_proxyport_exists(*names, targetip = "127.0.0.1", targetport = 8000, proxyaddress = "127.65.43.21", proxyport = 80):
    """ Checks whether register_named_proxyport has been used with the provided arguments.

        All arguments are the same as register_named_proxyport.
        If the named proxyport exists, return True. If no portion of the named proxyport is present, return False.
        If the named proxyport is incomplete, raise a RuntimeWarning. Incomplete named proxyports should be removed and re-registered.
    """
    netsh = False
    registered_netsh = get_netsh_portproxy()
    for entry in registered_netsh:
        ## ports should be converted to strings since get_netsh_portproxy returns strings
        if entry['listen']['address'] != proxyaddress: continue
        if entry['listen']['port'] != str(proxyport): continue
        if entry['connect']['address'] != targetip: continue
        if entry['connect']['port'] != str(targetport): continue
        netsh = True
        break

    hosts = python_hosts.Hosts()
    hostfile = False
    for entry in hosts.entries:
        if not entry.names: continue
        if not all(name in entry.names for name in names): continue
        if entry.address == proxyaddress:
            hostfile = True
            break

    if hostfile and netsh: return True
    if not hostfile and not netsh: return False
    warnings.warn(f"Incomplete Named Proxyport (netsh={netsh},hosts={hostfile})", RuntimeWarning)    

def get_netstat(*args, **kw):
    """ Returns the results of the netstat command.

        arguments are the same used by netstat and can be found here:
            https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/netstat
        Aliases are provided for readablity:
            all_conn    => -a
            e_stats     => -e
            numeric     => -n
            open_tcp    => -o
            protocol    => -p
            stats       => -s
            route       => -r

        Arguments except protocol are flags and can be passed as positional argument strings
        or can be set as keyword arguments using their alias.
        protocol must be specified as a keyword argument and should be an appropriate value
        per the Microsoft docs, or a list of such values.

        The return is a list of dictionaries with keys corresponding to the table headers returned by netstat.
    """
    MAPPING = {"all_conn":"-a", "-a":"-a",
               "e_stats":"-e", "-e":"-e",
               "numeric":"-n", "-n":"-n",
               "open_tcp":"-o", "-o":"-o",
               "stats":"-s", "-s":"-s",
               "route":"-r", "-r":"-r"}
    FLAGS = []
    for arg in args:
        if arg not in MAPPING:
            raise TypeError(f'get_natstat() got an unexpected argument "{arg}"')
        if arg in FLAGS:
            raise TypeError(f'get_netstat() got multiple values for argument "{a}"')
        FLAGS.append(MAPPING[arg])
    protocol = None
    if 'protocol' in kw:
        protocol = kw.pop('protocol')
    for k,v in kw.items():
        if k not in MAPPING:
            raise TypeError(f'get_natstat() got an unexpected argument "{k}"')
        if k in FLAGS:
            raise TypeError(f'get_netstat() got multiple values for argument "{k}"')
        if v: FLAGS.append(MAPPING[k])

    if protocol:
        VALIDPROTOS = ["tcp","udp","tcpv6","udpv6"]
        if "-s" in FLAGS: VALIDPROTOS.extend(["icmpv6","ipv6"])
        if isinstance(protocol, str): protocol = [protocol,]
        for p in protocol:
            if p not in VALIDPROTOS:
                raise ValueError(f'Invalid protocol: "{p}"')
        FLAGS.extend(["-p",]+protocol)

    result = subprocess.run(["netstat",]+FLAGS, capture_output = True, text = True, check = True)
    output = result.stdout.split("\n")[3:] ## Remove leading whitespace, "Active Connections", and whitespace header
    
    def processline(line):
        line = line.split("  ")
        return [v.strip() for v in line if v.strip()]
    keys = processline(output.pop(0))
    output = [dict(list(zip(keys,processline(line)))) for line in output if line.strip()]
    return output


IPTYPE = t.Union[ipaddress.IPv4Address,ipaddress.IPv6Address,int,str]
class PingResult(t.TypedDict):
    addr: t.Union[ipaddress.IPv4Address, ipaddress.IPv6Address]
    result: bool
def ping_range(*, startaddr: IPTYPE = None, endaddr: IPTYPE = None, addrlist: t.List[IPTYPE] = None, threads = 1) -> PingResult:
    """ Given either a start address and end address, or a list of addresses, ping each address and return if there was a response
    
        All addresses should be ipaddress.IPv4Address or IPv6Address instances, or addresses parsable by ipaddress.ip_address.
        If startaddress is provided, endaddress is required (and vice versa). addrlist should not supplied.
        Conversely, if addrlist is passed, startaddr and endaddr should not be declared.
        threads should be a positive integer and is used to spawn additional threads to speed up the process
        Returns a list of dictionary results containing { addr: ipaddress, result: boolean}
        where result is whether the ping was successful or not.
    """
    def is_address(addr):
        return isinstance(addr,(ipaddress.IPv4Address,ipaddress.IPv6Address))
    if startaddr and endaddr and addrlist:
        raise SyntaxError("ping_range should only be called with startaddr and endaddr, or addrlist by itself (not both)")
    if startaddr and not endaddr:
        raise SyntaxError("endaddr is required when calling ping_range with startaddr (use addrlist for a single address)")
    if endaddr and not startaddr:
        raise SyntaxError("Received endaddr but no startaddr")
    if not isinstance(threads,int) or threads <= 0:
        raise ValueError("threads should be a positive integer")
    if startaddr:
        try:
            if not is_address(startaddr): startaddr = ipaddress.ip_address(startaddr)
        except ValueError: raise ValueError("Could not convert startaddr to IP Address")
        try:
            if not is_address(endaddr): endaddr = ipaddress.ip_address(endaddr)
        except ValueError: raise ValueError("Could not convert endaddr to IP Address")
        addrlist = sum((list(network) for network in ipaddress.summarize_address_range(startaddr,endaddr)),[])
    else: ## addrlist
        try: addrlist = [ipaddress.ip_address(addr) if not is_address(addr) else addr for addr in addrlist]
        except ValueError: raise ValueError("addrlist contained non-IP Addresses")
    results = []

    with multiprocessing.Pool(threads) as p:
        results = p.map(_ping, addrlist)

    return results

def _ping(address):
    result = subprocess.run(["ping","-n","1",address.exploded], stdout = subprocess.PIPE ,  stderr = subprocess.PIPE, text = True)
    return dict(addr = address, result = result.returncode == 0 and "host unreachable" not in result.stdout)

if __name__ == "__main__":
    ## TODO: formalize
    from alcustoms.windows import run_as_admin
    def test_register_named_proxyport():
        if not is_admin():
            run_as_admin(["python",__file__])
        else:
            register_named_proxyport("foo.bar")

    def test_remove_named_proxyport():
        if not is_admin():
            run_as_admin(["python",__file__])
        else:
            remove_named_proxyport("foo.bar")

    def test_netstat():
        result = get_netstat("-a","-n", protocol = "tcp")
        from pprint import pprint
        pprint(result)

    def test_named_proxyport_exists():
        if not is_admin():
            run_as_admin(["python",__file__])
        else:
            print("Exists:",named_proxyport_exists("foo.bar"))
            register_named_proxyport("foo.bar")
            print("Exists:",named_proxyport_exists("foo.bar"))
            hosts = python_hosts.Hosts()
            hosts.remove_all_matching(name="foo.bar")
            hosts.write()   
            print("Exists:",named_proxyport_exists("foo.bar"))
            remove_named_proxyport("foo.bar")
            print("Exists:",named_proxyport_exists("foo.bar"))

    test_named_proxyport_exists()
    #test_register_named_proxyport()
    #test_remove_named_proxyport()
   