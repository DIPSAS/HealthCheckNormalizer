# Health Check Normalizer
This code fetches health checks for each endpoint related to the Testlab Environments and returns a normalized data set for each endpoint for use in e.g. dashboards.

This service runs within a Docker container, and needs to be built by exeucting the following:
```Bash
$ docker-compose build
```

When the image are built, start the container:
```Bash
$ docker-compose up -d
```


## Prerequisits
Docker and docker-compose must be working on the host.


## Configuration
The [configuration file](config.yaml) contains a section for _default values_ and specific configurations for each endpoint.

The syntax to use for a endpoint node which have only default values, looks like this:

```yaml
endpoints:
  hostname.domain.no:
```

If a specific configuration for the endpoints instead is preferred, the following could be applied instead:

```yaml
endpoints:
  hostname.domain.no:
    port: 1234
    request_uri: /api/endpointToGet
    proto: https
    method: get
```

The `method` parameter are at the moment only limited to `GET` requests, but will if needed be extended to support other methods such as `POST` requests.


## How does this work?
The Docker container runs the [start.sh](start.sh) script with the given [configuration file](config/config.yaml).

The given environments are defined within the configuration file.

The [start.sh](start.sh) script iterates through each environment and initiates the [main.py](main.py) against a given environment.

The [main.py](main.py) script iterates through each node host and retrieves all endpoints for a given environment.

Then each endpoint are probed against the given rules and a normalized JSON health format are outputted.
