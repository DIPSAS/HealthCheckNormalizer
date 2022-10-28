from urllib import request
import urllib.parse
import requests as req
import json
from requests.packages import urllib3
from modules.retriever import HCNRetriever

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HCNEndpoints:

    def __init__(self, endpoints, default_values):
        """ Base endpoint class for HealthCheckNormalizer.
        :param endpoints: Specific configuration endpoint values.
        :param default_values: Default configuration endpoint values.
        """
        self.endpoints = endpoints
        self.default_values = default_values
        self.buildEndpointNodeURLList()

    def buildEndpointNodeURLList(self):
        """ Build a list of URL's to each node endpoints."""
        node_endpoint_urls = []
        # Go through each endpoint
        for fqdn in self.endpoints:

            # Go through each param and check if a configuration parameter is set
            if self.endpoints[fqdn] is not None:
                for param in self.endpoints[fqdn]:
                    try:
                        self.endpoints[fqdn][param]
#                    except KeyError as e:
#                        endpoint_values = self.default_values[param]
                    finally:
                        if param == 'port':
                            port = self.endpoints[fqdn][param]
                        elif param == 'method':
                            method = self.endpoints[fqdn][param]
                        elif param == 'proto':
                            proto = self.endpoints[fqdn][param]
                        elif param == 'request_uri':
                            request_uri = self.endpoints[fqdn][param]

                endpoint_url = ''

                # Check if a protocol for the endpoint is defined in the configuration
                try:
                    endpoint_url = f"{proto}://"

                # If no protocol is defined, use default values
                except UnboundLocalError:
                    endpoint_url = f"{self.default_values['proto']}://"

                # Extend the endpoint URL with FQDN
                endpoint_url = endpoint_url + fqdn

                # Check if a port is defined in the configuration
                try:
                    endpoint_url = endpoint_url + f":{port}"

                # If no port is defined in the configuration, use default
                except UnboundLocalError:
                    endpoint_url = endpoint_url + f":{self.default_values['port']}"

                # Check if a request URI is set for the endpoint
                try:
                    endpoint_url = endpoint_url + request_uri

                # If no request URI is set for the endpoint, use default
                except UnboundLocalError:
                    endpoint_url = endpoint_url + self.default_values['request_uri']


            # No specific configuration found for the endpoint, use defaults
            else:
                endpoint_url = f"{self.default_values['proto']}://{fqdn}:{self.default_values['port']}{self.default_values['request_uri']}"

            node_endpoint_urls.append(endpoint_url)

        # Return the endpoint URL's
        self.node_endpoint_urls = node_endpoint_urls
        self.node_endpoint_fqdn = fqdn