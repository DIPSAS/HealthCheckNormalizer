class HCNLogging:

    def __init__(self, filename, file_content):
        """ Base builder class for HealthCheckNormalizer. This class is used for logging the normalized healthcheck.
        :param endpoint_url: URL to given endpoint. """
        self.filename = filename
        self.file_content = file_content
        self.writeToFile()

    def writeToFile(self):
        """ Writes given content to a logging file.
        :param filename: Filename for log (string)
        :param file_content: Content to write to file
        """
        with open(self.filename, "a") as logging_file:
            logging_file.write(f"{self.file_content}\n")