from serverdev.abc import AdministrativeCommon


class EsxiHost(AdministrativeCommon):
    def __init__(self, target, username, password):
        super(EsxiHost, self).__init__(target, username, password)

    def get_number_cpu(self):
        self.pout("esxcli hardware cpu list")
        return len(self.stdout("esxcli hardware cpu list | grep -i cpu:"))
