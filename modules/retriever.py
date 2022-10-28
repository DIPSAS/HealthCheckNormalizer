import requests as req
from requests.packages import urllib3

class HCNRetriever:

    def __init__(self, endpoint_url, timeout = 5, verify = False):
        """ Base retriever class for HealthCheckerNormalizer. Get's URL contents.
        :param: endpoint_url: URL to endpoint (string)
        """
        self.endpoint_url = endpoint_url
        self.verify = verify
        self.timeout = timeout
        self.getURLContent()

    def getURLContent(self):
        """ Retrieve content for a given URL. """
        self.content = req.get(self.endpoint_url, timeout=self.timeout, verify=self.verify)