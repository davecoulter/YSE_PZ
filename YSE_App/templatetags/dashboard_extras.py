from django import template
register = template.Library()

@register.filter(name='str_to_num')
def str_to_num(name):

	snid_numeric = ''
	for i in range(len(name)):
		try:
			float(n)
			snid_numeric += str(int(name[i]))
		except:
			if i != len(name) - 1:
				snid_numeric += '122'
			else:
				snid_numeric += '%03i'%ord(name[i])

	for i in range(7-len(name)):
		snid_numeric += '000'
				
	return(float(snid_numeric))

@register.filter(name='snidsort')
def snidsort(name):
	addnums = 7-len(name)

	return "".join([name[:4],"".join(['1']*addnums),name[4:]])

