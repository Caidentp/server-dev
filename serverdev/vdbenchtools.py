from serverdev.model import Client
import random


def get_random_number(maximum):
    """This function is used for randamizing which client performs io on a volume
    if it exists on more than one client. This is neccessary: if two clients
    perform io on the same volume, data corruption will occur.

    :param maximum: (int) Maximum number this function can return
    :return: int a number between 0 and the maximum parameter
    """
    return random.randint(0, maximum-1)


def validate_client_list(*args):
    """Helper function for instantiating WorkloadMaster. Ensures that only
    Client objects are being passed to WorkloadMaster.__init__().

    :param *args: (Client) arbitrary number of Client objects.
    """
    rtn = list()
    for arg in args:
        if type(arg) == Client:
            rtn.append(arg)
    return rtn


class WorkloadMaster(object):
    """Manages defining the vdbench workload for all clients.
    """
    def __init__(self, client_list):
        """For each client in client_list, set an attribute of that client.
        The attribute name is 'self.(client's hostname)' and the value is the
        Client object itself.

        :param client_list: (list[client]) list of instantiated Client objects.
        """
        for client in client_list:
            setattr(self, client.hostname(), client)

    def __len__(self):
        """How many clients this class was instantiated with.
        """
        return len(self.__dict__)

    def get_vdbench_wd_string(self, xfersize="4k", readpct="100",
                              seekpct="100", flags_str=""):
        """Create a vdbench workload definition for this client. Workload
        definition is the same for all storage definitions.

        :param xfersize: (str) transfer size for workload definition.
        :param readpct: (str) read percent for clueter I/O.
        :param seekpct: (str) random seek percent for cluster I/O.
        :return: str string defining workload for all storage definitions.
        """
        wd_base = "wd=wd1,sd=*,xfersize={},readpct={},seekpct={}"
        return wd_base.format(xfersize, readpct, seekpct) + flags_str

    def get_vdbench_rd_string(self, iorate="max", elapsed="10", interval="1",
                              flags_str=""):
        """Create a vdbench run definition for the workload definition.

        :param iorate: (str) workload specific I/O rate.
        """

    def get_all_volume_uids(self):
        """Returns all unique scsiNAADeviceID for all volumes on all clients
        that belong to this class as class attributes.

        :return: list[scsiNAADeviceID id's] Unique volume scsiNAADeviceID.
        """
        rtn = list()
        # host = client hostname, client = client object
        for host, client in self.__dict__.items():
            uid = client.get_volume_uids()  # get list of client's scsiNAADeviceID
            if uid is not None:
                rtn += uid
        return list(set(rtn))  # remove double entries by converting to a set

    def map_unique_volumes(self):
        """Maps volumes to their hosts in a dictionary. Because volumes can
        appear on more than one host, volume id is the key and the value is a
        list on hostnames that contain that volume.

        :return: dict[scsiNAADeviceID: list[hostnames]] list of hosts that have
                 the scsiNAADeviceID as an active vloume in their configuration.

        TODO: this is a heavy algorithm O^2. cache client.get_volume_uids()
        """
        unique_map = self.empty_volume_dict()  # dict[scsiNAADeviceID: list()]
        for host, client in self.__dict__.items():
            for volume in client.get_volume_uids():
                unique_map[volume].append(host)
        return unique_map

    def empty_volume_dict(self):
        """Helper method to cleanup self.map_unique_volumes(). Creates a
        dictionary object for mapping hosts to scsiNAADeviceID's.

        :return: dict[scsiNAADeviceID: list()] Dictionary of all scsiNAADeviceID's
                 on all clients mapped to an empty list.
        """
        return {k: list() for k in self.get_all_volume_uids()}

    def define_workload(self):
        """Create a list of unique volume id's on each client to define its io
        workload. Sets the workload attribute of each client. This method parses
        each unique scsiNAADeviceID, and creates the vdbench workload for each
        client accordingly. If a scsiNAADeviceID does exists on more than one
        client, it is only added to one client's workload to avoid data corruption.
        """
        for volume_id, host_list in self.map_unique_volumes().items():
            if host_list:
                # if the scsiNAADeviceID only appears on one host
                if len(host_list) == 1:
                    # get the client object by its attribute name
                    # can get a class attribute from a string by using eval()
                    client = eval("self.{}".format(host_list[0]))
                else:
                    # get a random index of the host_list
                    random_host = get_random_number(len(host_list))
                    client = eval("self.{}".format(host_list[random_host]))

                # get the path (/dev/mapper or PhysicalDrive) of a volume by
                # its lun ID
                path_to_volume = client.get_path_by_uid(volume_id)

                # append the path to the client's workload class attribute
                client.workload.append(path_to_volume)

    def write_master_conf_file(self):
        """Write the master vdbench configuration file. This method writes the
        entire vdbench file configuration for all clients defined as class
        attributes.
        """
        pass

    def start_rsh_on_clients(self):
        """For each client defined as a class attribute, call client.start_rsh()
        which will make sure that rsh is turned on for starting io on the client.
        If rsh is running on a client, it is started as a background process.
        """
        for key in self.__dict__.keys():
            client = eval("self.{}".format(key))
            client.start_rsh()

    def set_vdbench_master(self, index=0):
        """Choose a vdbench master to run the master vdparm file. By default,
        the master is the first class attribute set on the self instance. Vdparm
        file is copied from localhost to the master client.

        :param index: (int) list position of class attribute (Client objects)
                      to set as teh vdbench master.
        :return: dict['username': ..., 'password': ..., 'address': ..] master
                 client's ssh credentials
        """
        # get the client by index
        master = self.__dict__.values()[index]

        # get teh client ssh credentials
        creds = master.__dict__()

        # copy the master ennovar_vdparm.txt file from localhost to vdbench master
        os.system("sshpass -p {password} scp ennovar_vdparm.txt {username}@{address}:~/".format(**creds))
        return creds

    def start_vdbench(self, creds):
        """Start vdbench on all clients from the master client.

        :param creds: (Client.__dict__()) vdbench master ssh credentials
        """
        cmd = ssh_base + "'vdbench -f ennovar_vdparm.txt'"
        os.system(cmd.format(**creds))

    def stop_io(self):
        """Stop vdbench from running on all clients that belong to this class as
        class attributes.
        """
        for client in self.__dict__.values():
            client.stop_io()

    def main(self, start_io=True, write_file=True, copy_file=True, work_def=True):
        """Start rsh on all clietns, define a balanced workload accross all clients,
        write a master vdbench configuration file and copy it to the vdbench master
        client. Optionally, run io after vdbench master file is written and copied
        to master client.

        :param start_io: (bool) if True, io is automatically started after creating
                         vdparm file and copying it to master client
        """
        if len(self.__dict__) == 0:
            print("No clients to define workload for")
            return
        self.start_rsh_on_clients()
        if work_def:
            self.define_workload()
        if write_file:
            self.write_master_conf_file()
        if copy_file:
            creds = self.set_vdbench_master()
        if start_io:
            self.start_vdbench(creds)
