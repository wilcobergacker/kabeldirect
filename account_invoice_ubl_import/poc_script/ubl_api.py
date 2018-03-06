import requests
import base64
import json
#r = requests.post('https://secure.go2ubl.nl/api/v1/PurchaseStandard/PutDocument')


#Send PDF To UBL
def call(data, url):
    r = requests.post('http://go2ublv2-acc.azurewebsites.net/api/v1/%s'%url,
                      data= data,
                  headers={
                      'identifier':"0d36c979-1b66-42ca-bd51-850a0932c22a",
                      'code': 'odooexperts2UBL', 'token': 'EN67shOCXQ'
                  })
    return r
#r = call(data={
#    'KvkNumber': '55907431',
#    'ExternalId': 134,
#    'FileName': 'Voorbeeldfactuur.pdf',
#    'Content': base64.encodestring(open('Voorbeeldfactuur.pdf', 'r').read()),
#}, url ='PurchaseStandard/PutDocument')
r = call(data={
}, url='GetDocumentsToBeProcessed')
print r
print r.json()
print type(r.json())
for data in r.json()['Results']:
    f = call(data={'DocumentGUID':data['DocumentGuid']}, url='GetDocument')
    print f.content
    print "\n\n\n"


#get BL File BAck


