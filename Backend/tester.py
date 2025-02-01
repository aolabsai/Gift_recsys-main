
import http.client

conn = http.client.HTTPSConnection("real-time-amazon-data.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "723e3b8057msh611f8822fbca1b7p12867djsnb164e99788e3",
    'x-rapidapi-host': "real-time-amazon-data.p.rapidapi.com"
}

conn.request("GET", "/search?query=Phone&page=1&country=US&sort_by=RELEVANCE&product_condition=ALL&is_prime=false&deals_and_discounts=NONE", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))