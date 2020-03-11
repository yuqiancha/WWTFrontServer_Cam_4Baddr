import urllib
import http
import http.client
import json
import time

conn = http.client.HTTPSConnection("www.bohold.cn", port=443, timeout=10)
test_data = {'param': '1ACF湘A000101eb9001100001b100064000京'}

requrl = "https://www.bohold.cn/wwt-services-external/restful/server/position/secure/checkNewEnergy"
#checkNewEnergy
#receiveServerRequest
headerdata = {"Content-type": "application/json"}
conn.request('POST', requrl, json.dumps(test_data), headerdata)
response = conn.getresponse()
res = response.read()
print(res)

#time.sleep(2)
test_data = {'param': '1ACF湘A000101eb9001100001b100064000沪KR9888'}
requrl = "https://www.bohold.cn/wwt-services-external/restful/server/position/secure/receiveServerRequest"
conn.request('POST', requrl, json.dumps(test_data), headerdata)

response = conn.getresponse()

res = response.read()

print(res)