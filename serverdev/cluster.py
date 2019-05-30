import sys
from os import system, name, path, getcwd

from solidfire.common import LOG
from solidfire.factory import ElementFactory
from solidfire.models import CreateInitiator, CreateVolumeAccessGroupRequest


sfe = None


class TestSuite(object):
    """This class allows all subclasses to access other subclasses' properties."""
    def __init__(self, *args, **kwargs):
        LOG.setLevel(logging.WARNING)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_accounts(self):
        return sfe.list_accounts().accounts

    def get_account_ids(self):
        return [account.account_id for account in self.get_accounts()]

    def get_initiators(self):
        return sfe.list_initiators().initiators

    def get_vag_names(self):
        return [x.name for x in self.get_vags()]

    def get_initiator_ids(self):
        return [initiator.initiator_id for initiator in self.get_initiators()]

    def get_active_volumes(self):
        return sfe.list_active_volumes().volumes

    def get_volume_access_group_volumes(self, vag_id):
        """Return a list of all volumes id's that belong to a volume access group"""
        return [x.volume_id for x in self.get_active_volumes() if vag_id in x.volume_access_groups]

    def get_volume_access_group_initiators(self, vag_id):
        """Return a list of all initiator id's that belong to a volme access group"""
        return [x.initiator_id for x in self.get_initiators() if vag_id in x.volume_access_groups]

    def get_volume_ids(self):
        return [volume.volume_id for volume in self.get_active_volumes()]

    def get_deleted_volumes(self):
        return sfe.list_deleted_volumes().volumes

    def get_vags(self):
        return sfe.list_volume_access_groups().volume_access_groups

    def get_vag_ids(self):
        return [vag.volume_access_group_id for vag in self.get_vags()]

    def get_vag_volumes(self):
        temp = [vag.volumes for vag in self.get_vags()]
        vag_vol = [val for sublist in temp for val in sublist]
        return vag_vol

    def get_vag_initiators(self):
        temp = [vag.initiator_ids for vag in self.get_vags()]
        vag_init = [val for sublist in temp for val in sublist]
        return vag_init

    def get_initiators_without_vag(self):
        return list(set(self.get_initiator_ids()) - set(self.get_vag_initiators()))

    def get_volumes_without_vag(self):
        return list(set(self.get_volume_ids()) - set(self.get_vag_volumes()))

    def get_account_usernames(self):
        return [x.username for x in self.get_accounts()]

    def get_vag_by_id(self, vag_id):
        """Get a volume access group by its ID number

        :param vag_id: (int) Volume access group ID.
        :return: Volume access group if found, None otherwise.
        """
        for vag in self.get_vags():
            if vag.volume_access_group_id == vag_id:
                return vag
        return None

    def get_account_by_id(self, account_id):
        """Get an account by its id

        :param account_id: (int) Account ID.
        :return: Account if found, None otherwise.
        """
        for account in self.get_accounts():
            if account.account_id == account_id:
                return account
        return None

    def get_account_by_username(self, username):
        """Get an account by its username.

        :param username: (str) username of account to return.
        :return: Account if found, None otherwise.
        """
        for account in self.get_accounts():
            if account.username.lower() == username.lower():
                return account
        return None

    def get_vag_by_name(self, vag_name):
        """Get a volume access group by its name.

        :param vag_name: (str) name of volume access group to return.
        :return: Volume access group if found, none otherwise.
        """
        for vag in self.get_vags():
            if vag.name.lower() == vag_name.lower():
                return vag
        return None

    def print_vag_init_info(self):
        for vag in self.get_vag_ids():
            if len(self.get_volume_access_group_initiators(vag)) > 0:
                print("\nVolume Access Group ID: " + str(vag))
                print("Initiator Total: " + str(len(self.get_volume_access_group_initiators(vag))))
                for x in self.get_volume_access_group_initiators(vag):
                    print("Initiator ID: " + str(x))
        print("\n")

    def print_vag_vol_info(self):
        for vag in self.get_vag_ids():
            if len(self.get_volume_access_group_volumes(vag)) > 0:
                print("\nVolume Access Group ID: " + str(vag))
                print("Volume Total: " + str(len(self.get_volume_access_group_volumes(vag))))
                for x in self.get_volume_access_group_volumes(vag):
                    print("Volume ID: " + str(x))
        print("\n")


class TestAccounts(TestSuite):
    def __init__(self, **kwargs):
        super(TestAccounts, self).__init__(**kwargs)

    def create(self, accounts):
        """Create how ever many accounts you want

        :param account: (accounts) Number of accounts to create.
        """
        current_account = len(self.get_accounts())
        for x in range(1, accounts+1):
            sfe.add_account(username="Acc{}".format(current_account+x))

    def delete(self):
        """Delete all accounts created by this script. Note: this will also delete
        and purge any volumes created under accounts.
        """
        for account in tqdm(self.get_account_ids()):
            sfe.remove_account(account)

    def delete_account(self, account=None):
        """Delete a specific account. Note: Deleting an account will also delete
        and purge its volumes.

        :param account: (Account or int) Account or account id to delete.
        """
        if isinstance(account, int):
            account = self.get_account_by_id(account)
        if account is not None:
            for volume in account.volumes:
                sfe.delete_volume(volume)
            purge_all_volumes()
            sfe.remove_account(account.account_id)

    def delete_accounts(self, number_accounts):
        """Delete the first 'number_accounts' of accounts.

        :param number_accounts: (int) Number of accounts to delete.
        """
        active_accounts = self.get_accounts()
        if number_accounts >= len(self.get_accounts()):
            delete_all_accounts()
        else:
            for x in tqdm(range(number_accounts)):
                self.delete_account(active_accounts[x])


class TestInitiators(TestSuite):
    def __init__(self, **kwargs):
        super(TestInitiators, self).__init__(**kwargs)

    def create(self, initiators=0, WPN=None):
        """Create how ever many initiators you want

        :param initiators: (int) Number of initiators to create.
        :param WPN: (str or list[str]) Single WPN to create or list of WPNs to create.
        """
        initiator_list = list()
        current_initiator = len(self.get_initiators())
        print("Creating initiators")
        if isinstance(WPN, str):
            if len(WPN) >= 16:
                initiator_list.append(CreateInitiator(name=WPN))
        elif isinstance(WPN, list):
            for initiator_name in tqdm(WPN):
                if len(initiator_name) >= 16:
                    initiator_list.append(CreateInitiator(name=initiator_name))
        else:
            for x in tqdm(range(1, initiators+1)):
                kwargs = {'name': "00:00:00:00:00:00:00:1{}".format(current_initiator+x)}
                initiator_list.append(CreateInitiator(**kwargs))
        sfe.create_initiators(initiator_list)

    def modify(self, method=None, vag_id=None, vag_id2=None, user_list=None):
        # This part of the code removes the initiators out of the desired VAG
        if user_list.lower() == 'all':
            init_list = self.get_volume_access_group_initiators(vag_id)
            sfe.remove_initiators_from_volume_access_group(volume_access_group_id=vag_id, initiators=init_list, delete_orphan_initiators=False)
        else:
            init_list = map(int, user_list.split())
            sfe.remove_initiators_from_volume_access_group(volume_access_group_id=vag_id, initiators=init_list, delete_orphan_initiators=False)

        # This part of the code moves the initiators to the desired VAG
        if method == '2' or method == "move":
            sfe.add_initiators_to_volume_access_group(vag_id2, init_list)

    def delete(self):
        """Delete all initiators created by this script"""
        sfe.delete_initiators(self.get_initiator_ids())


class TestVolumes(TestSuite):
    def __init__(self, **kwargs):
        super(TestVolumes, self).__init__(**kwargs)
        self.q = Queue()

    def create(self, volumes):
        """Create how ever many volumes you want

        :param volumes: (int) Number of volumes to create.
        """
        kwargs = {"total_size": 80*1024**3, "enable512e": True}
        current_account_index = 0

        try:
            # get the first account id
            current_account = self.get_account_ids()[current_account_index]
        except IndexError:
            # if no accounts exist, create one
            sfe.add_account(username="AccFirst1")
            current_account = self.get_account_ids()[current_account_index]

        print("Creating Volumes")
        for x in tqdm(range(volumes)):
            # Create a new account if there are not enough to create the requested number of volumes
            if current_account_index == len(self.get_accounts()):
                sfe.add_account(username="AccCreateVolumes{}".format(current_account_index))

            # Switch to the next account if current one already has 2000 volumes
            while len(sfe.get_account_by_id(current_account).account.volumes) >= 2000:
                current_account_index += 1
                # Create a new account if there are not enough to create the requested number of volumes
                if current_account_index == len(self.get_accounts()):
                    sfe.add_account(username="AccCreateVolumes{}".format(current_account_index))
                current_account = self.get_account_ids()[current_account_index]
            sfe.create_volume(name="Testvolume{}".format(x+1), account_id=current_account, **kwargs)

    def _delete_threader(self):
        """Target member function for multithreading volumes to delete"""
        while True:
            sfe.delete_volume(self.q.get())
            self.q.task_done()

    def delete(self):
        """Delete all volumes created by this script"""
        self.q = Queue()

        # create 128 threads to execute _delete_threader at the same time
        for x in range(128):
             thread = Thread(target=self._delete_threader)
             thread.daemon = True
             thread.start()
        # add each volume id to the queue to be processed by _delete_threader
        for volume in self.get_active_volumes():
            self.q.put(volume.volume_id)
        self.q.join()

    def _purge_threader(self):
        """Target member function for multithreading volumes to purge"""
        while True:
            sfe.purge_deleted_volume(self.q.get())
            self.q.task_done()

    def purge(self):
        """Purge all volumes created by this script"""
        self.q = Queue()

        # create 128 threads to execute _purge_threader at the same time
        for x in range(128):
             thread = Thread(target=self._purge_threader)
             thread.daemon = True
             thread.start()
        # add each deleted volume id to the queue to be processed by _purge_threader
        for volume in self.get_deleted_volumes():
            self.q.put(volume.volume_id)
        self.q.join()

    def modify(self, method=None, vag_id=None, vag_id2=None, user_list=None):
        # This part of the code removes the initiators out of the desired VAG
        if user_list.lower() == 'all':
            vol_list = self.get_volume_access_group_volumes(vag_id)
            sfe.remove_volumes_from_volume_access_group(volume_access_group_id=vag_id, volumes=vol_list)
        else:
            vol_list = map(int, user_list.split())
            sfe.remove_volumes_from_volume_access_group(volume_access_group_id=vag_id, volumes=vol_list)

        # This part of the code moves the initiators to the desired VAG
        if method == '2' or method == "move":
            sfe.add_volumes_to_volume_access_group(vag_id2, vol_list)

    def delete_volumes_without_vag(self, number_of_vols):
        """Delete specified number of volumes that do not belong to a vag.

        :param number_of_vols: (int) Number of volumes to delete. If number exceeds
                               number of volumes without vag, all will be deleted.
        """
        volumes_without_vag = self.get_volumes_without_vag()
        if number_of_vols >= len(volumes_without_vag):
            for volume in tqdm(volumes_without_vag):
                self.delete_volume_by_id(volume)
        else:
            for volume in tqdm(range(number_of_vols)):
                self.delete_volume_by_id(volumes_without_vag[volume])

    def delete_volume_by_id(self, vol_id):
        """Delete a single volume by its id.

        :param vol_id: (int) Volume id of volume to delete.
        """
        assert(vol_id in self.get_volume_ids())
        sfe.delete_volume(vol_id)


class TestVAGs(TestSuite):
    def __init__(self, **kwargs):
        super(TestVAGs, self).__init__(**kwargs)

    def create(self, vags, assign_init=0, assign_vol=0):
        """Create volume access groups. Optionally assign random initiators and
        volumes to each volume access group to be created.

        :param vags: (int) Number of volumes access groups to create.
        :param assign_init: (int) Number of initiators to assign to each vag.
        :param assign_vol: (int) Number of volumes to assign to each vag.
        """
        current_VAG = len(self.get_vags()) + 1
        print("Creating VAGs and assigning volumes and initiators")

        for x in tqdm(range(vags)):
            init_without_vag = self.get_initiators_without_vag()
            vols_without_vag = self.get_volumes_without_vag()
            init_to_add = list()
            vols_to_add = list()

            for y in range(assign_init):
                if y == len(init_without_vag):
                    break  # end loop if more initiators are requested than exist
                init_to_add.append(init_without_vag[y])

            for y in range(assign_vol):
                if y == len(vols_without_vag):
                    break  # end loop if more volumes are requested than exist
                vols_to_add.append(vols_without_vag[y])

            kwargs = {'name': "TestVAG{}".format(current_VAG+x), 'initiators': init_to_add, 'volumes': vols_to_add}
            sfe.create_volume_access_group(**kwargs)

    def delete(self, num_to_delete=None):
        """Delete all Volume Access Groups created by script"""
        print("Deleting VAGs")
        if num_to_delete is None or num_to_delete >= len(self.get_vag_ids()):
            for vag_id in tqdm(self.get_vag_ids()):
                sfe.delete_volume_access_group(vag_id, False)
        else:
            active_vags = self.get_vag_ids()
            for x in tqdm(range(num_to_delete)):
                sfe.delete_volume_access_group(active_vags[x], False)

    def add_initiators(self, initiators, vag_id):
        """Add initiators that aren't assigned to a Volume Access Group to a Volume Access Group

        :param initiators: (int) Number of initiators to add to VAG.
        :param vag_id: (int) Volume access group to add initiators to.
        """
        if len(self.get_vags()) == 0:
            print('\nNo VAGs exist. Create a VAG and try again.\n')
            return

        initiators_without_vag = self.get_initiators_without_vag()
        initiators_list = list()
        for x in range(initiators):
            if x == len(initiators_without_vag):
                print("Exceeded the available amount of initiators.")
                break  # end loop if more initiators are requested than exist
            if (x + len(initiators_without_vag)) >= 128:
                print("Exceeded the available amount of initiators a VAG can hold.")
                break  # end loop if VAG is at max capacity of initiators
            initiators_list.append(initiators_without_vag[x])
        sfe.add_initiators_to_volume_access_group(vag_id, initiators_list)

    def add_volumes(self, volumes, vag_id):
        """Add volumes that aren't assigned to a Volume Access Group to a Volume Access Group

        :param volumes: (int) Number of volumes to add to VAG.
        :param vag_id: (int) Volume access group to add volumes to.
        """
        if len(self.get_vags()) == 0:
            print('\nNo VAGs exist. Create a VAG and try again.\n')
            return

        volumes_without_vag = self.get_volumes_without_vag()
        volumes_list = list()
        for x in range(volumes):
            if x == len(volumes_without_vag):
                print("Exceeded the available amount of volumes.")
                break  # end loop if more volumes are requested than exist
            if (x + len(volumes_without_vag)) >= 2000:
                print("Exceeded the available amount of initiators a VAG can hold.")
                break  # end loop if VAG is at max capacity of volumes.
            volumes_list.append(volumes_without_vag[x])
        sfe.add_volumes_to_volume_access_group(vag_id, volumes_list)

    def modify(self, method=None, vag_id=None, vag_id2=None):
        initiators = TestInitiators()
        volumes = TestVolumes()

        initiators.modify(method=method, vag_id=vag_id, vag_id2=vag_id2, user_list="all")
        volumes.modify(method=method, vag_id=vag_id, vag_id2=vag_id2, user_list="all")

    def print_vags_and_vols_list(self):
        """Print a list of volume access groups and how many volumes each has."""
        print('VAG ID   Active volumes\n')
        for vag in self.get_vags():
            print('{}\t {}'.format(vag.volume_access_group_id, len(vag.volumes)))

    def print_vags_and_inits_list(self):
        """Print a list of volume access groups and how many initiators each has."""
        print('VAG ID   Active initiators\n')
        for vag in self.get_vags():
            print('{}\t {}'.format(vag.volume_access_group_id, len(vag.initiators)))

    def print_vags_and_vols_inits_list(self):
        """Print a list of volume access groups and how many initiators/volume each has."""
        print('VAG ID   Active initiators   Active volumes\n')
        for vag in self.get_vags():
            print('{}\t\t {}\t\t {}'.format(vag.volume_access_group_id, len(vag.initiators), len(vag.volumes)))

    def delete_volumes_from_vag(self, vag=None, volumes=0):
        """Delete volumes from a specific volume access group.

        :param vag: (Volume Access group) VAG to delete volumes from.
        :param volumes: (int) Number of volumes to delete.
        """
        if vag is not None:
            if volumes >= len(vag.volumes):
                for volume_id in tqdm(vag.volumes):
                    sfe.delete_volume(volume_id)
                vag = self.get_vag_by_id(vag.volume_access_group_id)  # Refresh after deleting
                for volume_id in tqdm(vag.deleted_volumes):
                    sfe.purge_deleted_volume(volume_id)
            else:
                for x in tqdm(range(volumes)):
                    vag = self.get_vag_by_id(vag.volume_access_group_id)  # Refresh after deleting
                    sfe.delete_volume(vag.volumes[0])
                for x in tqdm(range(volumes)):
                    vag = self.get_vag_by_id(vag.volume_access_group_id)  # Refresh after deleting
                    sfe.purge_deleted_volume(vag.deleted_volumes[0])
        else:
            volumes_without_vag = self.get_volumes_without_vag()
            if volumes >= len(volumes_without_vag):
                for volume_id in tqdm(volumes_without_vag):
                    sfe.delete_volume(volume_id)
                for volume_id in tqdm(volumes_without_vag):
                    sfe.purge_deleted_volume(volume_id)

    def delete_initiators_from_vag(self, vag=None, initiators=0):
        """Delete initiators from a specific volume access group.

        :param vag: (Volume Access group) VAG to delete volumes from.
        :param initiator: (int) Number of initiator to delete.
        """
        init_list = []
        if vag is not None:
            if initiators >= len(vag.initiators):
                sfe.delete_initiators(vag.initiator_ids)
            else:
                for x in tqdm(range(initiators)):
                    init_list.append(vag.initiator_ids[x])
                sfe.delete_initiators(init_list)

    def delete_vag(self, vag):
        """Delete a single volume access group by either its name or id"""
        if isinstance(vag, int):
            sfe.delete_volume_access_group(vag, False)
        else:
            sfe.delete_volume_access_group(vag.volume_access_group_id, False)


def set_global_sfe(hostname=None, username=None, password=None):
    """Create a connection to the cluster that all classes have access to.
    This function must be called before you instantitate any other classes in this
    file. This is so that all classes work with the same connection to the cluster.

    :param username: (str) Username to connect to cluster with.
    :param password: (str) Password to connect to cluster with.
    """
    if not hostname:
        hostname = valid_input(str, "Enter IP address or hostname of cluster (10.194.79.248): ")
    global sfe
    try:
        sfe = ElementFactory.create(hostname, username, password)
    except Exception:
        print('\nFailed to connect to host {}: invalid input or session timeout\n'.format(hostname))
        return


def valid_input(input_type, message):
    """Ensure that the user enters input of te appropriate Python type.
    Will continue to prompt user until an appropriate answer is input.

    :param input_type: Type class that user input should convert to (int, str, et cetera).
    :param message: Message to be displayed when prompting user for input.

    :return: User input of valid type.

    :example:
        >>> valid_input(int, "Please input an integer: ")
    """
    user_input = None
    while not isinstance(user_input, input_type):
        try:
            if sys.version[0] == '2':
                user_input = input_type(raw_input(message))
            else:
                user_input = input_type(input(message))
            # user_input = input_type(input(message))
        except Exception:
            continue
    return user_input
