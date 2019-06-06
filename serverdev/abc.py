from serverdev.const import *
from subprocess import Popen, PIPE
from platform import system as system_platform
import os


def script_host_platform():
    return system_platform().lower()


class SshCommon(object):
    """Defines common functions for working with ssh.

    :attr username: (str) SSH username for resource object.
    :attr password: (str) SSH password for resource object.
    :attr target: (str) IP address of resource object.
    """
    def __init__(self, target, username, password):
        self.username = username
        self.password = password
        self.target = target

    def __dict__(self):
        return {
            'username': self.username,
            'password': self.password,
            'target': self.target
        }

    def platform(self):
        """Get the operating system platform of a server 'linux' or 'windows'.

        :return: str the platform of remote server operating system.
        """
        cmd = 'echo "" | python -c "from platform import system; print(system())"'
        return self.stdout(cmd)[0].lower()

    def _format_ssh_command(self, command):
        """Format a command to with SSH credentials for self.

        :param command: (str) command to execute on remote server.
        :return: str SSH command formated with credentials.
        """
        if script_host_platform() == LINUX:
            creds = ssh_base_linux.format(**self.creds())
        else:
            creds = ssh_base_windows.format(**self.creds())
        cmd = creds + "'{}'"
        cmd = cmd.format(command)
        return cmd

    def stdout(self, command):
        """Execute a command on a remote machine and read the output. Output is
        returned as a list of strings where each index represents a line of the
        output.

        :param command: (str) command to execute on remote server.
        :return: list[str] list of lines of output from command.
        """
        cmd = self._format_ssh_command(command)
        pipe = Popen(cmd, stdout=PIPE, shell=True)
        output = pipe.communicate()[0]
        if type(output) == bytes:
            return output.decode("utf-8").split('\n')[:-1]
        return output

    def execute(self, command):
        """Execute a command on a remote server without returning the output.

        :param command: (str) command to execute on remote server.
        """
        cmd = self._format_ssh_command(command)
        os.system(cmd)

    def pout(self, command):
        """Print a command's output to the console.

        :param command: (str) command to execute.
        """
        for line in self.stdout(command):
            print(line)

    def creds(self):
        """Make the passing of login credentials to functions more obvious. Use
        **self.creds() rather than **self.__dict__.

        :return: dict[target, username, password]
        """
        return self.__dict__()


class InformationCommon(SshCommon):
    """More restrictive than AdministrativeCommon. Used for getting general"""
    def __init__(self, target, username, password):
        super(InformationCommon, self).__init__(target, username, password)

    def hostname(self):
        """Get the hostname of a remote server.

        :return: str hostname of remote server.
        """
        return self.stdout('hostname')[0]

    def online(self):
        """Ensure that the host is online before attempting to connect to it.

        :return: bool True if host is online, False otherwise.
        """
        ping = self.stdout("ping -c 2 -W 1 {}".format(self.target))
        if len(ping) > 0:
            return True
        return False


class AdministrativeCommon(InformationCommon):
    """Defines administrative functions for operating on resource objects.
    """
    def __init__(self, target, username, password):
        super(AdministrativeCommon, self).__init__(target, username, password)

    def start_process(self, p_name):
        """Run a process in the background on linux and powershell servers.

        :param p_name: (str) Name of protocol to enable.
        """
        cmd = None
        if self.platform() == LINUX:
            cmd = "{} &".format(p_name)
        elif self.platform() == WIN32:
            cmd = "saps -NoNewWindow {}".format(p_name)
        if cmd is not None:
            self.execute(cmd)

    def scp(self, src_path, dst_path):
        """Use scp to move a file from localhost to remote server.

        :param src_path: (str) location of file on localhost.
        :param dst_path: (str) location of file on remote host.
        """
        kwargs = {
            'username': self.username,
            'password': self.password,
            'target': self.target,
            'src_path': src_path,
            'dst_path': dst_path
        }
        os.system(scp_base.format(**kwargs))
