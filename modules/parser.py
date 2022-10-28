import json
import xml.etree.ElementTree as ET
import re
from bs4 import BeautifulSoup
import xmltodict


class HCNParser:

    def __init__(self, data):
        """ Base parser class for Health Check Normalizer.
        :param endpoint_url: URL to endpoint (string)
        """
        self.data = data

    def detectHCFormat(self):
        """ Detect health check format. """
        if self.isJson(self.data) is True:
            return 'json'
        elif self.isXml(self.data) is True:
            return 'xml'
        elif self.isHtml(self.data) is True:
            return 'html'
        else:
            return 'unk'


    @staticmethod
    def isJson(data):
        """ Check if given format is JSON. """
        try:
            json_object = json.loads(data)
        except ValueError:
            return False
        else:
            return True


    @staticmethod
    def isXml(data):
        """ Check if given format is XML. """
        if re.search("<\?xml", data) or re.search(" xmlns", data):
            return True
        else:
            return False

    @staticmethod
    def isHtml(data):
        """ Check if given format is HTML. """
        if re.search("<html>", data.lower()) or re.search("<!DOCTYPE html>", data.lower()):
            return True
        else:
            return False

    @staticmethod
    def htmlToJson(data):
        """ Convert data from HTML to JSON. """
        pass

    @staticmethod
    def xmlToJson(data):
        """ Convert data from XML to JSON. """
#        parsed = json.dumps(xmltodict.parse(data), indent = 2)
#        parsed = xmltodict.parse(data)
        parsed = BeautifulSoup(data, "xml")
        return parsed
        #pass