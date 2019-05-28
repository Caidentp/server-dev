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
