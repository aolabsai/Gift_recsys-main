import requests
import numpy as np
import json
#16+10+3
url = "https://api.aolabs.ai/v0dev/kennel/agent"

LABEL = "0000000000"
uid= "rafayel@aolabs.aitestingMum"
payload = {
    "kennel_id": "gift-recsys-1",  # use kennel_name entered above
    "agent_id": uid,   # enter unique user IDs here, to call a unique agent for each ID
    "request": "story",
}

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "X-API-KEY": "KzZbXbaahd1ElPO5Rtyv3a1ejHlw3Kn848c9SA1J"
}

response = requests.post(url, json=payload, headers=headers)
response_dict = json.loads(response.text)
print(response_dict["state"])
print(type(response_dict))

print(response_dict.keys())
story = response_dict["story"]
story = list(story)

story = np.asarray(story, dtype="int")
print(story.shape)
reshape = np.reshape(story, [277, 16+16+ 10+ 3])
