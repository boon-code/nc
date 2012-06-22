import android
import socket
import nc
import os

droid = android.Android()

HOST = '127.0.0.1'
LOCHOST = '192.168.1.200'
PORT = 7642
DIR = '/sdcard/download'

_KEY_PUSH = 'push'
_KEY_PULL = 'pull'
_KEY_CANCEL = 'cancel'
_KEY_EXIT = 'exit'
_KEY_IP = 'change ip'
_KEY_DIR = 'change dir'

_client = nc.NcClient(HOST, PORT)
_work = DIR


def _dialog_result(list):
    ret = droid.dialogGetResponse()
    val = u''
    which = u''
    try:
        if not (ret is None):
            res = ret.result
            if isinstance(res, dict):
                if res.has_key('which'):
                    which = res['which']
                
                if res.has_key('item'):
                    nr = res['item']
                    val = list[nr]
                elif res.has_key('value'):
                    val = res['value']
        
        return (which, val)
    except IndexError:
        print "Index Error"
        return _dialog_result(list)


def file_dialog(items):
    droid.dialogCreateInput()
    droid.dialogSetNegativeButtonText('cancel')
    droid.dialogSetItems(items)
    droid.dialogShow()
    ret = _dialog_result(items)
    
    if ret[0] == 'negative':
        return None
    return ret[1]


def pull_dialog():
    list = _client.list()
    print list
    list = list[1]
    ret = file_dialog(list)
    
    if not (ret is None):
        _client.get(ret, _work)


def push_dialog():
    ret = file_dialog(os.listdir(_work))
    
    if not(ret is None):
        _client.put(ret, _work)


def ip_dialog():
    droid.dialogCreateInput('ip: ', 'ip', LOCHOST)
    droid.dialogSetNegativeButtonText('cancel')
    droid.dialogSetPositiveButtonText('set')
    droid.dialogShow()
    
    ret = _dialog_result([])
    if ret[0] == 'positive':
        global _client
        print ret[1]
        _client = nc.NcClient(ret[1], PORT)


def dir_dialog(path):
    
    items = ['.', '..']
    for i in os.listdir(path):
        filepath = os.path.join(path, i);print filepath
        if os.path.isdir(filepath):
            items.append(filepath)
    droid.dialogCreateInput()
    droid.dialogSetNegativeButtonText('cancel')
    droid.dialogSetPositiveButtonText('ok')
    droid.dialogSetItems(items)
    droid.dialogShow()
    
    ret = _dialog_result(items)
    if ret[0] == 'positive':
        return path
    elif ret[0] == 'negative':
        return None
    else:
        f = os.path.realpath(os.path.join(path, ret[1]))
        return dir_dialog(f)


def work_dialog():
    
    global _work
    droid.makeToast("working dir is %s" % _work)
    res = dir_dialog(_work)
    if not (res is None):
        _work = res
        print "set working dir to %s" % _work


def main_dialog():
    droid.dialogCreateInput()
    items = [_KEY_PUSH, _KEY_PULL, _KEY_IP
            , _KEY_DIR, _KEY_CANCEL, _KEY_EXIT]
    droid.dialogSetItems(items)
    droid.dialogShow()
    ret = _dialog_result(items)[1]
    if ret == _KEY_PUSH:
        push_dialog()
        return True
    elif ret == _KEY_PULL:
        pull_dialog()
        return True
    elif ret == _KEY_EXIT:
        _client.exit()
        return False
    elif ret == _KEY_IP:
        ip_dialog();
        return True
    elif ret == _KEY_DIR:
        work_dialog()
        return True
    else:
        return False


running = True
while running:
    try:
        droid.wakeLockAcquireFull()
        running = main_dialog()
        droid.wakeLockRelease()
    except socket.error:
        droid.makeToast("socket exception")
