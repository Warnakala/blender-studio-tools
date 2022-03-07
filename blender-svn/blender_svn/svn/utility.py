import os

from . import common, local, remote, constants

def get_client(url_or_path, *args, **kwargs):
    if url_or_path[0] == '/':
        return local.LocalClient(url_or_path, *args, **kwargs)
    else:
        return remote.RemoteClient(url_or_path, *args, **kwargs)

def get_common_for_cwd():
    path = os.getcwd()
    uri = 'file://{}'.format(path)

    cc = common.CommonClient(uri, constants.LT_URL)
    return cc
