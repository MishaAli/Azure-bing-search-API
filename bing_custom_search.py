from requests import exceptions
import argparse
import requests
from PIL import Image
import os.path
import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()

ap = argparse.ArgumentParser()
ap.add_argument("-s", "--search", required=True,
                help="search search to search Bing Image API for")
args = vars(ap.parse_args())
print(args)

# environment variable defined inside of .env file
subscription_key = os.getenv("BingSearchSubscriptionKey")
print(subscription_key)
if not subscription_key:
    print("Please set BingSearchSubscriptionKey")
    quit()

#initialization
max_search_results = 250
count = 50

endpoint = "https://api.bing.microsoft.com/v7.0/images/search"
search_term = args["search"]
headers = {"Ocp-Apim-Subscription-Key": subscription_key}
params = { "q": search_term,
           "offset": 0, 
           "count": count,
           "imageType": "photo"
         }

EXCEPTIONS = {IOError, FileNotFoundError, exceptions.RequestException, exceptions.HTTPError, exceptions.ConnectionError,
              exceptions.Timeout}

# search Request - Api call

print("[INFO] Bing Search Request for '{}'".format(search_term))
try:
    search = requests.get(endpoint, headers=headers, params=params)
    search.raise_for_status()

    results = search.json()
    estNumResults = min(results["totalEstimatedMatches"], max_search_results)
    print("[INFO] {} total results for '{}'".format(estNumResults,
                                                search_term))
except Exception as ex:
    raise ex

# initialize the total number of images downloaded thus far
total = 0

# loop over the estimated number of results in `count` groups
for offset in range(0, estNumResults, count):
    # update the search parameters using the current offset, then
    # make the request to fetch the results
    print("[INFO] making request for group {}-{} of {}...".format(
        offset, offset + count, estNumResults))

    params["offset"] = offset
    search = requests.get(endpoint, headers=headers, params=params)
    search.raise_for_status()
    results = search.json()

    print("[INFO] saving images for group {}-{} of {}...".format(
        offset, offset + count, estNumResults))

    # loop over the results
    for v in results["value"]:
        # try to download the image
        try:
            # make a request to download the image
            print("[INFO] fetching: {}".format(v["contentUrl"]))

            r = requests.get(v["contentUrl"], timeout=30)

            # build the path to the output image - set as png
            ext = ".png"
            dataset_path = Path.cwd() / "dataset" / search_term
            path_out_img = dataset_path / f"{str(total).zfill(8)}{ext}"
            dataset_path.mkdir(parents=True, exist_ok=True)

            # write the image to disk
            f = open(path_out_img, "wb")
            f.write(r.content)
            f.close()

        # catch any errors that would not unable us to download the
        # image
        except Exception as e:
            # check to see if our exception is in our list of
            # exceptions to check for
            if type(e) in EXCEPTIONS:
                print("[INFO] skipping: {}".format(v["contentUrl"]))
                continue

        try:
            im = Image.open(path_out_img)
        except IOError:
            # filename not an image file, so it should be ignored
            print("[INFO] deleting: {}".format(path_out_img))
            os.remove(path_out_img)
            continue

        # update the counter
        total += 1
