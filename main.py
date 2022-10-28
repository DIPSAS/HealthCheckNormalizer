import json
from modules.config import Config
from modules.hcnendpoints import HCNEndpoints
from modules.retriever import HCNRetriever
from modules.parser import HCNParser
from modules.hcnbuilder import HCNBuilder
from modules.hcnlogging import HCNLogging
import sys
import re
import os.path
import datetime

# Set configuration file
cfg_file = sys.argv[2]

# Create datetime function for use later
def utc_now():
    utc_now = datetime.datetime.utcnow()
    utc_timestamp = utc_now.strftime("%Y-%m-%dT%H:%M:%SZ")
    return utc_timestamp

# Start of program
if __name__ == "__main__":

    if not os.path.exists(cfg_file):
        print(f"Error: Configuration file does not exist.")
        sys.exit(1)
    else:
        print(f"{utc_now()} Found config file: {cfg_file}")

    try:
        environment_filter = sys.argv[1].replace('\n', '').replace('\r', '').replace('\?', '')
    except:
        print(f"Usage: python3 {sys.argv[0]} <environment (as defined in config.yaml)>")
        sys.exit(1)
    finally:
        print(f"{utc_now()} Running HealthCheckNormalizer for environment {environment_filter}")

    # Initialize objects
    cfg = Config(cfg_file)

    # Set default values
    default_values = cfg.default_values

    # Global values
    global_values = cfg.global_values

    # Rules
    rules_healthy = cfg.rules_healthy
    rules_degraded = cfg.rules_degraded
    rules_unhealthy = cfg.rules_unhealthy

    # Set environment names
    environments = cfg.environments

    # Set logging file
    if global_values['main_logs']:
        log_file = f"{global_values['logging_directory']}/{global_values['main_logging_file']}"

    # Check if the given environment exists within the configuration file
    if environment_filter in environments:
        pass
    else:
        error_msg = f"{utc_now()} Error: Non-existing environment {environment_filter} in config file."
        if global_values['main_logs']:
            HCNLogging(log_file, error_msg)

        print(error_msg)
        cfg.printDebugMessage(environments, f"Environments:")
        sys.exit(1)

    # Get endpoints URL from configuration file
    endpoints = cfg.node_fqdns
    hcn = HCNEndpoints(endpoints, default_values)

    # Debug mode on: Print all endpoint node URL's (list)
    cfg.printDebugMessage(hcn.node_endpoint_fqdn, 'ENDPOINTS')

    # Prepare relevant endpoints (Degraded and Unhealthy)
    hcn_healthcheck = HCNBuilder()
    unique_id = 0

    # Go through each URL
    for node_endpoint_url in hcn.node_endpoint_urls:
        try:
            node_endpoint_list = HCNRetriever(node_endpoint_url, global_values['connection_timeout'])

            # Debug mode on: Print endpoint URL's
            cfg.printDebugMessage(node_endpoint_url, 'ENDPOINT')

            # Check if HTTP code is between 200 and 299 (success msgs)
            if node_endpoint_list.content.status_code >= 200 and node_endpoint_list.content.status_code <= 299:
                node_endpoint_content = node_endpoint_list.content.text

            # Raise exception if not
            else:
                raise Exception("Server returned status code:", node_endpoint_list.content.status_code)
        except NameError:
            error_msg = f"{utc_now()} Error: Node not found: {node_endpoint_url}"
            if global_values['main_logs']:
                HCNLogging(log_file, error_msg)

            print(error_msg)
            sys.exit(1)
        except Exception as e:
            error_msg = f"{utc_now()} Error: Unable to retrieve node endpoint list from URL: {node_endpoint_url}"
            if global_values['main_logs']:
                HCNLogging(log_file, error_msg)
            print(error_msg)
            sys.exit(1)
        finally:
            try:
                parse = HCNParser(node_endpoint_content)

                # Detect format for health check
                format = parse.detectHCFormat()

                # Debug mode on: Print endpoint content
                cfg.printDebugMessage(f'{node_endpoint_content}', f'ENDPOINT CONTENT ({format})')

                # Check if the endpoint node URL is JSON format
                # Convert if neccessary
                if format == 'json':
                    json_content = node_endpoint_content
                elif format == 'xml':
                    json_content = parse.xmlToJson(node_endpoint_content)
                elif format == 'html':
                    json_content = parse.htmlToJson(node_endpoint_content)
                elif format == 'unk':
                    error_msg = f"{utc_now()} Unknown format for health check: {node_endpoint_url}"
                    if global_values['main_logs']:
                        HCNLogging(log_file, error_msg)
                    cfg.printDebugMessage(f"{utc_now()} Unknown format for health check: {node_endpoint_url}", 'ENDPOINT PARSER')

                # Parse the endpoints if enlisted in JSON format
                try:
                    json_content = json.loads(json_content)
                except:
                    error_msg = f"{utc_now()} Error while parsing JSON content. Valid JSON format not found for endpoint {node_endpoint_url}"
                    if global_values['main_logs']:
                        HCNLogging(log_file, error_msg)
                    cfg.printDebugMessage(f"{utc_now()} Error while parsing JSON content. Valid JSON format not found for endpoint {node_endpoint_url}", 'ENDPOINT PARSER')
                finally:

                    # Iterate through the retrieved JSON content
                    for json_dict in json_content:

                        # Retrieve essential service and server information
                        service_base_url = json_dict['serviceBaseUrl'].lower()
                        service_name = json_dict['serviceName']
                        server_fqdn = re.sub("((http|https):\/\/)|(:[0-9].*$)", "", service_base_url).lower()
                        server_hostname = re.sub("\.[A-Za-z0-9].*$", "", server_fqdn).lower()
                        node_endpoint = re.sub("((http|https):\/\/)|(:[0-9].*$)", "", node_endpoint_url).lower()
                        environment_name = endpoints[node_endpoint]['environment']

                        # Check if the given environment is equal to this entry
                        if environment_filter == environment_name:

                            # If debug is `True` - print the service and server information
                            debug_msg = f"SERVICE NAME: {service_name}\nSERVICE BASE URL: {service_base_url}\nSERVER FQDN: {server_fqdn}\nSERVER HOSTNAME: {server_hostname}\nJSON:\n{json_dict}\nENVIRONMENT:\n{environment_name}"
                            cfg.printDebugMessage(debug_msg, 'SERVER AND SERVICE INFO')

                            # Iterate through each endpoint for the given service
                            for endpoint in json_dict['endpoints']:

                                unique_id = int(unique_id+1)
                                endpoint_id = unique_id

                                # Build endpoint address and retrieve data from endpoint
                                service_endpoint_url = service_base_url + endpoint['endpointAddress']
                                cfg.printDebugMessage(f"{utc_now()} Attempting to retrieve endpoint: {service_endpoint_url}")
                                service = HCNRetriever(service_endpoint_url, global_values['connection_timeout'])

                                # Check if the service returns http_code between 200 - 299
                                if service.content.status_code >= 200 and service.content.status_code <= 299:

                                    # Convert endpoint data to text, load parser and detect format for health check
                                    healthcheck = service.content.text
                                    svc_parse = HCNParser(healthcheck)
                                    svc_format = svc_parse.detectHCFormat()

                                    # Check if given rules (string) exists in URL
                                    rules_healthy_url = bool([element for element in rules_healthy['in_url'] if(element in service_endpoint_url)])

                                    # Check if given rules (string) exists in reply
                                    rules_healthy_reply = bool([element for element in rules_healthy['url_expected_reply'] if(element in healthcheck)])

                                    # Check if the health check format is HTML
                                    if svc_format == 'html':
                                        json_service_content = parse.htmlToJson(healthcheck)
                                        service_status = 'HEALTHY'
                                        cfg.printDebugMessage(f"HTML detected:\n{service_endpoint_url}", 'SERVICE STATUS')

                                    # Check if the health check format is XML
                                    elif svc_format == 'xml':
                                        json_service_content = parse.xmlToJson(healthcheck)
                                        service_status = 'HEALTHY'
                                        cfg.printDebugMessage(f"XML detected:\n{service_endpoint_url}", 'SERVICE STATUS')

                                    # Check if rules applies to both URL and the reply
                                    elif rules_healthy_url is True and rules_healthy_reply is True:
                                        service_status = 'HEALTHY'
                                        cfg.printDebugMessage(f"Healthy rules matched on URL and reply: {service_endpoint_url}", 'SERVICE STATUS')

                                    # JSON - Check if the format is JSON and the rules applies for URL
                                    elif svc_format == 'json' and rules_healthy_url is True:
                                        json_service_content = json.loads(healthcheck.lower())
                                        service_status = json_service_content['status'].upper()
                                        service_status_code = json_service_content['statuscode']

                                        # Check if service status is matching status code for unhealthy service
                                        if service_status == rules_unhealthy['status_code']:
                                            service_status = 'UNHEALTHY'

                                        # Check if service status is matching status code for degraded service
                                        elif service_status == rules_degraded['status_code']:
                                            service_status = 'DEGRADED'

                                        # Check if service status is matching status code for healthy service
                                        elif service_status == rules_healthy['status_code']:
                                            service_status = 'HEALTHY'

                                        cfg.printDebugMessage(f"JSON detected:\n{service_endpoint_url}\nSERVICE STATUS: {service_status} ({service_name})\n{healthcheck}", 'SERVICE STATUS:')

                                    # Check if the reply is blank
                                    elif len(healthcheck) == 0:
                                        service_status = 'HEALTHY'
                                        cfg.printDebugMessage(f"Healthy health check, length of health check is 0: {service_endpoint_url}", 'SERVICE STATUS')

                                    # Check if the rules only applies for the reply
                                    elif rules_healthy_reply is True:
                                        service_status = 'HEALTHY'
                                        cfg.printDebugMessage(f"Healthy rules matched on reply only: {service_endpoint_url}", 'SERVICE STATUS')

                                    # Unknown format for health check (e.g. format not implemented)
                                    elif svc_format == 'unk':
                                        service_status = 'unknown'
                                        cfg.printDebugMessage(f"Unknown format for health check: {service_endpoint_url}", 'SERVICE STATUS')

                                    # Check if the global values indicates if healthy endpoints should be shown in generated health check
                                    if (global_values['show_active'] and service_status == 'HEALTHY') or service_status == 'DEGRADED':
                                        hcn_healthcheck.buildHealthCheck(server_hostname, service_endpoint_url, service_name, service_status, endpoint_id, environment_name)

                                else:
                                    # generate health check data
                                    service_status = 'UNHEALTHY'
                                    hcn_healthcheck.buildHealthCheck(server_hostname, service_endpoint_url, service_name, service_status, endpoint_id, environment_name)
                                    debug_msg = f"SERVICE NAME: {service_name} | SERVER HOSTNAME: {server_hostname} | SERVER FQDN: {server_fqdn} | SERVICE ENDPOINT URL: {service_endpoint_url}"
                                    cfg.printDebugMessage(debug_msg, 'SERVICE STATUS')

                                # Print a compact debug message if chosen in configuration
                                compact_debug_msg = f"{service_status} {server_fqdn} {service_name} {service_endpoint_url}"
                                cfg.printDebugMessage(compact_debug_msg)

                                # Print full debug message if chosen
                                cfg.printDebugMessage(f"SERVICE STATUS: {service_status} ({service_name}): {service_endpoint_url}", 'SERVICE STATUS')

            except NameError:
                error_msg = f"{utc_now()} Error: Node not found: {node_endpoint_url}"
                if global_values['main_logs']:
                    HCNLogging(log_file, error_msg)
                print(error_msg)


    # Dump JSON to file
    if global_values['write_to_file']:
        json_dump = json.dumps(hcn_healthcheck.getHealthCheck(), indent=2)
        output_dir = f"{global_values['endpoint_dir']}"
        if not os.path.exists(output_dir):
            error_msg = f"{utc_now()} Error: Output directory does not exist: {output_dir}"
            if global_values['main_logs']:
                HCNLogging(log_file, error_msg)
            print(error_msg)
        else:
            output_file = f"{output_dir}/{environment_filter}-endpoints.json"
            with open(output_file, "w") as file:
                if file.write(json_dump):
                    print(f"{utc_now()} Successfully dumped JSON structure to JSON file: {output_file}")

    print(f"{utc_now()} Script finished for {environment_filter}")