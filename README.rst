server-dev
==========

Description
-----------

This is a Python wrapper for vCenter Management REST API 6.5.

API documentation: https://caidenpyle.com/api_docs.html

Quick Start
-----------

Pull the module into your namespace:

.. code-block:: python

    from serverdev import *

First, you need to authenticate to the vCenter server:

.. code-block:: python

    VCenterSession('your vCenter ip', 'your username', 'your password')

Great! Now we can interact with objects on the vCenter server:

.. code-block:: python

    host = EsxHost('host ip', 'host username', 'host password')
    virtual_machines = host.get_vms()

We can execute functions on esx hosts and virtual machines alike:

.. code-block:: python

    host.enter_maint_mode()
    for vm in virtual_machines:
        vm.poweroff()

