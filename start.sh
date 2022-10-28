#!/bin/bash
CONFIG_FILE=$1
WEBSERVER_PORT=$2
DATE=$(date +%Y-%m-%dT%H:%M:%SZ)
LOGS_DIRECTORY=$(grep "logging_directory" $CONFIG_FILE | awk '{ print $2 }')
SH_LOGS=$(grep 'sh_logs' $CONFIG_FILE | awk '{ print $2 }')
SH_LOGGING_FILE=$(grep 'sh_logging_file' $CONFIG_FILE | awk '{ print $2 }')

function check_config_existence() {
  if [ ! -f $CONFIG_FILE ]; then
    if [ $SH_LOGS = True ]; then
      echo "${DATE} Error: Configuration file \"${CONFIG_FILE}\" not found. Program exited." >> "${LOGS_DIRECTORY}/${SH_LOGGING_FILE}"
    fi

    echo "${DATE} Error: Configuration file \"${CONFIG_FILE}\" not found. Program exited."
    return 1
  else
    return 0
  fi
}

function check_config_format() {
  if [[ $(egrep -i 'default_values:|global_values:|rules_degraded_services:|rules_unhealthy_services:|rules_healthy_services:|endpoints:' $CONFIG_FILE | wc -l) -ne 6 ]]; then
    if [ $SH_LOGS = True ]; then
      echo "${DATE} Error: Invalid configuration file format." >> "${LOGS_DIRECTORY}/${SH_LOGGING_FILE}"
    fi
    echo "${DATE} Error: Invalid configuration file format."
    return 1
  else
    return 0
  fi
}

if [ -z $CONFIG_FILE ]; then
  echo "Usage: bash $0 <HealthCheckNormalizer config.yaml path> <webserver port>"
  exit
fi

# Check if configuration file exists - if not, quit the program
check_config_existence
if [ $? -ne 0 ]; then
  exit
fi

# Check configuration format
check_config_format
if [ $? -eq 0 ]; then
  if [[ $(egrep -i 'webserver_logs|webserver_logging_file' $CONFIG_FILE | wc -l) -ne 2 ]]; then
    if [ $SH_LOGS = True ]; then
      echo "${DATE} Error: Invalid configuration file format: missing either 'webserver_logs' or 'webserver_logging_file'" >> "${LOGS_DIRECTORY}/${SH_LOGGING_FILE}"
    fi
    echo "${DATE} Error: Invalid configuration file format: missing either 'webserver_logs' or 'webserver_logging_file'"
    exit
  fi
fi

if [[ $(ps aux|grep "python3 -m http.server ${WEBSERVER_PORT}" | grep -v grep | wc -l) -ne 1 ]]; then
  cd data/
  echo "${DATE} Attempting to start Python webserver"
  WEBSERVER_LOGGING=$(grep "webserver_logs" $CONFIG_FILE | awk '{ print $2 }')
  if [ $WEBSERVER_LOGGING = True ]; then
    WEBSERVER_LOG_FILE=$(grep "webserver_logging_file" $CONFIG_FILE | awk '{ print $2 }')
    PYTHONUNBUFFERED=x python3 -m http.server $WEBSERVER_PORT &>> "${LOGS_DIRECTORY}/${WEBSERVER_LOG_FILE}" &
  else
    python3 -m http.server $WEBSERVER_PORT > /dev/null &
  fi
else
  echo "${DATE} Python webserver already running on port ${WEBSERVER_PORT}"
fi

HCN_DIR=$(dirname $CONFIG_FILE)

# Start program
while true; do

  # Check config existence - exit if the file does not exist
  check_config_existence
  if [ $? -ne 0 ]; then
    exit
  fi

  # Redeclare date
  DATE=$(date +%Y-%m-%dT%H:%M:%SZ)

  # Check config format
  check_config_format
  if [ $? -eq 0 ]; then
#  if [[ $(egrep -i 'default_values:|global_values:|rules_degraded_services:|rules_unhealthy_services:|rules_healthy_services:|endpoints:' $CONFIG_FILE | wc -l) -eq 6 ]] && [ -f $CONFIG_FILE ]; then

    # Retrieve environment count and throw error msg if no environments found
    ENVIRONMENT_COUNT=$(grep 'environment:' $CONFIG_FILE | grep -v '#' | awk '{ print $2 }' | sed -e 's/"//g' | sort | uniq | wc -l)
    if [ $ENVIRONMENT_COUNT -eq 0 ]; then

      # Check if errors should be appended to log
      if [ $SH_LOGS = True ]; then
        echo "${DATE} Error: No environments found in config file. Add 'environment:' key below a given FQDN." >> "${LOGS_DIRECTORY}/${SH_LOGGING_FILE}"
      fi
      echo "${DATE} Error: No environments found in config file. Add 'environment:' key below a given FQDN."
    else
      echo "${DATE} Environment(s) found: ${ENVIRONMENT_COUNT}"
    fi

    # Get list of environments from config file and iterate through each environment
    grep 'environment:' $CONFIG_FILE | grep -v '#' | awk '{ print $2 }' | sed -e 's/"//g' | sort | uniq | while read -r ENVIRONMENT
    do

      # Retrieve PID for the Python process for the given environment
      # Allowed characters for environment name including alphanumeric characters: - .
      ENV=$(echo $ENVIRONMENT | tr -cd "\-\.[A-Z0-9a-z]")
      PID=$(ps aux | grep python3 | grep 'main.py' | grep "$ENV" | awk '{ print $2 }')

      # If the process is not running, a Python process will be initiated
      if [[ ! -z $PID ]]; then
        echo "${DATE} HealthCheckNormalizer already running for $ENVIRONMENT"
      else
        echo "${DATE} Attempting to start HealthCheckNormalizer for $ENVIRONMENT"
        # python3 "${HCN_DIR}/main.py" "$ENV" "$CONFIG_FILE" > /dev/null &
        python3 "/app/main.py" "$ENV" "$CONFIG_FILE" &
      fi
    done

  else
    echo "${DATE} Error: An error occured either with the config file format or the existence of the config file."
  fi
  sleep 5
done