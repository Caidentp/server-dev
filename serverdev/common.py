from solidfire.factory import ElementFactory


def set_sfe(target, username, password):
    """Set the global MVIP object for interacting with the cluster.

    :param username: (str) mvip username.
    :param password: (str) mvip passowrd.
    :param target: (str) mvip ip address.
    """
    return ElementFactory.create(target, username, password)
