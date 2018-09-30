def any_running(arg_dict, arg_hosts, arg_name):
	found_any = False
	for item in arg_hosts:
		if arg_name in arg_dict[item]['services']:
			if arg_dict[item]['services']['arg_name']['state'] == 'running':
				found_any = True
	return found_any

class FilterModule(object):
	def filters(self):
		return {'any_running': any_running}

#  vim: set ts=8 sw=8 tw=0 noet :
