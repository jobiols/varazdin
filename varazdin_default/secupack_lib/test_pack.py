from secupack import SecupackClient
import pprint
pp = pprint.PrettyPrinter(indent=4)

client = SecupackClient(user='jobiols', password='123')

data = client.get_package_by_code('1')
print 'data',data
 
pack = data.get('pack',False)
if pack:
    completed = pack.get('completed','False')
    print completed
    if completed:
        actions = pack.get('actions',False)
        for act in actions:
            value = act.get('value',False)
            for val in value:
                print val.get('action',False)
                print val.get('cnt',False)
                print val.get('tipo',False)




kk = pp.pprint(data)

print kk

