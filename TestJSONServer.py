import urllib
import http
import http.client
import json


conn =http.client.HTTPConnection("192.168.0.115:8083",timeout=10)
test_data = {'param': 'haha'}

requrl = "http://192.168.0.115:8083/wwt-services-external/restful/server/position/secure/receiveServerRequest"

headerdata = {"Content-type": "application/json"}

conn.request('POST', requrl, json.dumps(test_data), headerdata)

SendToWebstr = '/wwt-services-external/restful/server/position/secure/receiveServerRequest/'

#conn.request("POST",urllib.parse.quote(SendToWebstr))

response = conn.getresponse()

res = response.read()

print(res)