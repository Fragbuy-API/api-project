import requests

response = requests.get("http://155.138.159.75/api/v1/art-orders-health")
print(response.status_code)
print(response.json())