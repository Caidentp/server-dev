from serverdev.const import LINUX
from serverdev.abc import AdministrativeCommon


class Client(AdministrativeCommon):
    """Class for interacting with client resources.
    """
    def __init__(self, target, username, password):
        super(Client, self).__init__(target, username, password)
        self.vdbench_options = list()
        # self.volume_dict  Created by calling self.get_volume_dict()

    def get_volume_paths(self):
        """Returns the path name of each active volume on this client.

        :return: list[str] mpaths if client is linux, physicaldrives if client
                 is Windows
        """
        if self.platform() == LINUX:
            cmd = "multipath -ll | egrep -oi 'mpath[a-z]+'"
            return ["/dev/mapper/" + x for x in self.stdout(cmd)]
        # Windows clients
        regex = " | egrep -oi '\\\\.\\PhysicalDrive[0-9]+'"
        cmd = "'{}'".format('iscsiapp --disk_map') + regex
        return self.stdout(cmd)

    def get_lun_ids(self):
        """Returns the volume id's of each active volume on this client

        :return: list[str] active scsiNAADeviceID's on this client.
        """
        if self.platform() == LINUX:
            ids = self.stdout("multipath -ll | egrep -oi \"\\([a-z0-9]+\\)\"")
            return [x[1:-1] for x in ids]  # remove parentheses from ends
        # Windows clients
        ids = self.stdout("'iscsiapp --disk_map' | egrep -oi 'VolumeID: [0-9]+'")
        ids = [int(x[10:]) for x in ids]
        return [get_uid_by_volume_id(x) for x in ids]

    def get_volume_dict(self):
        """Maps each volume's path (physicaldrive on Windwos, mpath on linux)
        name to its scsiNAADeviceID in a python dictionary (hashtable).
        This function will create a class attribute 'self.volume_dict' so
        that it only has to be run once due to the high performance cost.

        :return: dict[path: scsiNAADeviceID] (keys = (str), values = (str))
        """
        rtn = None
        try:
            # memoization is used due to constly function
            rtn = self.volume_dict
        # if function has not been called before
        except AttributeError:
            paths = self.get_volume_paths()
            uids = self.get_lun_ids()
            if paths is not None and uids is not None:
                rtn = dict(zip(paths, uids))
            else:
                rtn = dict()
            # set a class attribute so that this algorithm only needs to be run
            # once. If function is called a second time, class attribute is
            # returned rather than running algorithm again.
            self.volume_dict = rtn
        return rtn

    def get_path_by_uid(self, uid):
        """Reverse dictionary lookup. Return an scsiNAADeviceID by its volume id
        used within the solidfire sdk.

        :param uid: (int) Volume ID of a LUN used by solidfire sdk.
        :return: str scsiNAADeviceID toat matches a volume ID.
        """
        for key, value in self.get_volume_dict().items():
            if value == uid:
                return key
        return None

    def get_vdbench_sd_list(self, flags_str="", counter=0):
        """Get a list of storage definitions for all volumes on this client.
        Additionally, you can add vdparm storage definition flags to the
        storage definition strings returned by this function.

        !NOTE! Do NOT add 'openflags=o_direct' to flags string, it is detected
               and added automaticallw when necessary.

        :param flags_str: (str) vdparm flags to add to each storage definition.
        :param counter: (int) counting index to start at when naming storage
                        definitions. Used for multi-host config files.
        :return: list[str] vdparm stoarge definitions strings.
        """
        if self.platform() == LINUX:
            flags_str += "openflags=o_direct"
        sd_string = "{}," + flags_str

        sd_string_list = list()
        for index, path in enumerate(self.get_volume_paths()):
            sd_number = index + counter
            sd = "sd-{},lun={}".format(sd_number, path)
            sd_string_list.append(sd_string.format(sd))
        return sd_string_list

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

    def stop_io(self):
        """Kill vdbench on this client to stop io from running.
        """
        if self.platform() == LINUX:
            self.execute('pkill vdbench; pkill java')
        else:
            # Windows clients
            self.execute("Stop-Process -Name 'java' -Force")


class Node(AdministrativeCommon):
    """Class for interacting with node resources.
    """
    def __init__(self, target, username, password):
        super(Node, self).__init__(target, username, password)
