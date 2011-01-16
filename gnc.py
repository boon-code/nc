import android
import nc
import os

droid = android.Android()

HOST = '127.0.0.1'
PORT = 7642
DIR = '/sdcard/download'

_KEY_PUSH = 'push'
_KEY_PULL = 'pull'
_KEY_CANCEL = 'cancel'
_KEY_EXIT = 'exit'

_client = nc.NcClient(HOST, PORT)


def _dialog_result(list):
	ret = droid.dialogGetResponse()
	item = u''
	which = u''
	if not (ret is None):
		result = ret.result
		if isinstance(res, dict):
			if res.has_key('which'):
				which = res['which']
			elif res.has_key('item'):
				nr = res['item']
				item = list[nr]
	return (which, item)


def file_dialog(items):
	droid.dialogCreateInput()
	droid.dialogSetNegativeButton('cancel')
	droid.dialogSetItems(items)
	droid.dialogShow()
	ret = _dialog_result(items)
	
	if ret[0] == 'negative':
		return None
	return ret[1]


def pull_dialog():
	list = _client.list()
	ret = file_dialog(list[1])
	
	if not (ret is None):
		_client.get(ret, DIR)


def push_dialog():
	ret = file_dialog(os.listdir(DIR))
	
	if not(ret is None):
		path = os.path.join(DIR, ret)
		_client.put(path) 


def main_dialog():
	droid.dialogCreateInput()
	items = [_KEY_PUSH, _KEY_PULL, _KEY_CANCEL, _KEY_EXIT]
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
	else:
		return False


running = True
while running:
	running = main_dialog()
