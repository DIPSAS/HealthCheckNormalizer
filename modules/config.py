from distutils.command.config import config
import yaml

class Config:

    def __init__(self, config_file):
        """ Base class for reading configuration parameters from config file.
        :params config_file: configuration file (string)
        """
        self.config_file = config_file
        self.readConfigFile()

    def readConfigFile(self):
        """ Read configuration file into object. """
        with open(self.config_file, 'r') as file:
            configuration = yaml.safe_load(file)

        # Retrieve endpoint URL's
        self.node_fqdns = configuration['endpoints']

        # Set default values
        self.default_values = configuration['default_values']

        # Set global values
        self.global_values = configuration['global_values']

        # Set rules
        self.rules_healthy = configuration['rules_healthy_services']
        self.rules_degraded = configuration['rules_degraded_services']
        self.rules_unhealthy = configuration['rules_unhealthy_services']

        # Get environments
        self.environments = []
        for node_fqdn in self.node_fqdns:
            if self.node_fqdns[node_fqdn]['environment'] not in self.environments:
                self.environments.append(self.node_fqdns[node_fqdn]['environment'])

    def printDebugMessage(self, debug_msg, header_title = None):
        """ Check if debug mode is activated and print debugging. """
        if self.global_values['debug_full'] is True:
            print(f"DEBUG [{header_title}]:")
            print(debug_msg)

        if self.global_values['debug_compact'] is True and header_title is None:
            print(debug_msg)