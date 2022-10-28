class HCNBuilder:

    def __init__(self):
        """ Base builder class for HealthCheckNormalizer. This class builds the normalized healthcheck.
        :param endpoint_url: URL to given endpoint. """

        self.healthcheck = {
            "name": "HealthCheckNormalizer",
            "values": []
        }

    def buildHealthCheck(self, hostname, url, service_name, state, id, environment_name):
        """ Build a JSON normalized healthcheck structure and append it
        to the values list.
        :param hostname: Hostname for node (string)
        :param url: URL to endpoint on given node (string)
        :param service_name: Service name (string)
        :param state: Service state (string)
        """
        json_content = {
            "id": id,
            "hostname": hostname,
            "url": url,
            "service_name": service_name,
            "state": state,
            "environment": environment_name
        }

        self.healthcheck['values'].append(json_content)

    def getHealthCheck(self):
        """ Get the healthcheck for debugging purposes. """
        return self.healthcheck