from serverdev.common import LINUX
from serverdev.abc import AdministrativeCommon


class Client(AdministrativeCommon):
    """Class for interacting with client resources.
    """
    def __init__(self, target, username, password):
        super(Client, self).__init__(target, username, password)

    def get_paths(self):
        """Returns the path name of each active volume on this client.

        :return: list[str] mpaths if client is linux, physicaldrives if client
                 is Windows
        """
        if self.platform() == LINUX:
            return self.stdout("multipath -ll | egrep -oi 'mpath[a-z]+'")
        # Windows clients
        regex = " | egrep -oi '\\\\.\\PhysicalDrive[0-9]+'"
        cmd = "'{}'".format('iscsiapp --disk_map') + regex
        return self.stdout(cmd)

    def configure_for_vdbench(self):
        """Prepare a client for vdbench to run on it.
        """
        self.start_rsh()

    def rsh_is_running(self):
        """Check if rsh is running on a client or not. This method is used by
        self.start_rsh() to ensure that it returnsself.

        :return: bool True if rsh is running, False otherwise
        """
        running = self.stdout('ps -ef | grep -v grep | grep -e "vdbench rsh"')
        if len(running) == 0:
            return False
        return True

    def start_rsh(self):
        """Ensure that rsh is running in the background on this client. If rsh
        is not running, start it; if rsh is running, return. Rsh is required to
        be running on clients for multiple host vdparm configuration files.
        """
        if not self.rsh_is_running():
            self.start_process("vdbench rsh")



class Node(AdministrativeCommon):
    """Class for interacting with node resources.
    """
    def __init__(self, target, username, password):
        super(Node, self).__init__(target, username, password)
