# FalconPy API Service Collections Reference

This document provides a comprehensive reference for all service collections in the FalconPy SDK, covering every collection from **Alerts** to **Zero Trust Assessment**. Each section below corresponds to a specific CrowdStrike Falcon API service collection, including all available API operations (endpoints) within that collection. For each operation, the official PEP 8 method name, endpoint details, required scope, accepted parameters, and example usage (both in Service Class and Uber Class styles) are provided exactly as in the official FalconPy documentation. 

**Table of Contents**  
- [Alerts](#alerts)  
- [API Integrations](#api-integrations)  
- [ASPM](#aspm)  
- [Certificate Based Exclusions](#certificate-based-exclusions)  
- [Cloud Connect AWS](#cloud-connect-aws)  
- [Cloud Snapshots](#cloud-snapshots)  
- [Compliance Assessments](#compliance-assessments)  
- [Configuration Assessment](#configuration-assessment)  
- [Configuration Assessment Evaluation Logic](#configuration-assessment-evaluation-logic)  
- [Container Alerts](#container-alerts)  
- [Container Detections](#container-detections)  
- [Container Images](#container-images)  
- [Container Packages](#container-packages)  
- [Container Vulnerabilities](#container-vulnerabilities)  
- [Correlation Rules](#correlation-rules)  
- [CSPM Registration](#cspm-registration)  
- [Custom IOAs](#custom-ioas)  
- [Custom Storage](#custom-storage)  
- [D4C Registration](#d4c-registration)  
- [DataScanner](#datascanner)  
- [Delivery Settings](#delivery-settings)  
- [Detects](#detects)  
- [Device Control Policies](#device-control-policies)  
- [Discover](#discover)  
- [Downloads](#downloads)  
- [Drift Indicators](#drift-indicators)  
- [Event Streams](#event-streams)  
- [Exposure Management](#exposure-management)  
- [Falcon Complete Dashboard](#falcon-complete-dashboard)  
- [Falcon Container](#falcon-container)  
- [Falcon Intelligence Sandbox](#falcon-intelligence-sandbox)  
- [FDR (Falcon Data Replicator)](#fdr-falcon-data-replicator)  
- [FileVantage](#filevantage)  
- [Firewall Management](#firewall-management)  
- [Firewall Policies](#firewall-policies)  
- [Flight Control](#flight-control)  
- [Foundry LogScale](#foundry-logscale)  
- [Host Group](#host-group)  
- [Host Migration](#host-migration)  
- [Hosts](#hosts)  
- [Identity Protection](#identity-protection)  
- [Image Assessment Policies](#image-assessment-policies)  
- [Incidents](#incidents)  
- [Installation Tokens](#installation-tokens)  
- [Intel (Threat Intelligence)](#intel-threat-intelligence)  
- [Intelligence Feeds](#intelligence-feeds)  
- [IOA Exclusions](#ioa-exclusions)  
- [IOC (Indicators of Compromise v2)](#ioc-indicators-of-compromise-v2)  
- [IOCs (Deprecated Indicators of Compromise v1)](#iocs-deprecated-indicators-of-compromise-v1)  
- [Kubernetes Protection](#kubernetes-protection)  
- [MalQuery](#malquery)  
- [Message Center](#message-center)  
- [ML Exclusions](#ml-exclusions)  
- [Mobile Enrollment](#mobile-enrollment)  
- [MSSP (Flight Control)](#mssp-flight-control)  
- [NGSIEM](#ngsiem)  
- [OAuth2](#oauth2)  
- [ODS (On Demand Scan)](#ods-on-demand-scan)  
- [Overwatch Dashboard](#overwatch-dashboard)  
- [Prevention Policy](#prevention-policy)  
- [Quarantine](#quarantine)  
- [Quick Scan](#quick-scan)  
- [Quick Scan Pro](#quick-scan-pro)  
- [Real Time Response](#real-time-response)  
- [Real Time Response Admin](#real-time-response-admin)  
- [Real Time Response Audit](#real-time-response-audit)  
- [Recon](#recon)  
- [Report Executions](#report-executions)  
- [Response Policies](#response-policies)  
- [Sample Uploads](#sample-uploads)  
- [Scheduled Reports](#scheduled-reports)  
- [Sensor Download](#sensor-download)  
- [Sensor Update Policy](#sensor-update-policy)  
- [Sensor Usage](#sensor-usage)  
- [Sensor Visibility Exclusions](#sensor-visibility-exclusions)  
- [Spotlight Evaluation Logic](#spotlight-evaluation-logic)  
- [Spotlight Vulnerabilities](#spotlight-vulnerabilities)  
- [Tailored Intelligence](#tailored-intelligence)  
- [ThreatGraph](#threatgraph)  
- [Unidentified Containers](#unidentified-containers)  
- [User Management](#user-management)  
- [Workflows](#workflows)  
- [Zero Trust Assessment](#zero-trust-assessment)  

> **NOTE:** In all the example code below, API credentials (`client_id` and `client_secret`) are passed as parameters when instantiating the service class or Uber class. **Do not hard-code API credentials** or customer identifiers in your source code. The examples assume these values are provided (e.g., from environment variables or secure input) rather than hard-coded.

---

## Alerts

**Description:** Provides access to CrowdStrike Falcon **Alerts** APIs, allowing retrieval of alert data and performing actions on alerts.

**Available Operations:**

- `PostAggregatesAlertsV1` (PEP 8: `get_aggregate_alerts_v1`) – Retrieve aggregates for alerts across all CIDs. **(Deprecated:** superseded by `PostAggregatesAlertsV2`**)**  
- `PostAggregatesAlertsV2` (PEP 8: `get_aggregate_alerts_v2`) – Retrieve aggregates for alerts across all CIDs.  
- `PatchEntitiesAlertsV2` (PEP 8: `update_alerts_v2`) – Perform actions on alerts identified by alert ID(s) in the request. **(Deprecated:** superseded by `PatchEntitiesAlertsV3`**)**  
- `PatchEntitiesAlertsV3` (PEP 8: `update_alerts_v3`) – Perform actions on alerts identified by alert ID(s) in the request.  
- `PostEntitiesAlertsV1` (PEP 8: `get_alerts_v1`) – Retrieve all alerts given their IDs. **(Deprecated:** superseded by `PostEntitiesAlertsV2`**)**  
- `PostEntitiesAlertsV2` (PEP 8: `get_alerts_v2`) – Retrieve all alerts given their IDs.  
- `GetQueriesAlertsV1` (PEP 8: `query_alerts_v1`) – Search for alert IDs that match a given query. **(Deprecated:** superseded by `GetQueriesAlertsV2`**)**  
- `GetQueriesAlertsV2` (PEP 8: `query_alerts_v2`) – Search for alert IDs that match a given query.  

### PostAggregatesAlertsV1

Get alert aggregates as specified by a JSON request body. **Deprecated operation:** This operation has been superseded by `PostAggregatesAlertsV2` and is now deprecated. Developers should move to the new operation as soon as possible.

**PEP 8 method name:** `get_aggregate_alerts_v1` (alias: `get_aggregate_alerts`)

**Endpoint:** `POST /alerts/aggregates/alerts/v1`  

**Required Scope:** `alerts:read`  

**Content-Type:** 
- Consumes: `application/json`  
- Produces: `application/json`  

**Parameters (Keyword Arguments):**  
- **body** (`list[dict]`): Full request body payload in JSON/dictionary format.  
- **date_ranges** (`list[dict]`): Applies to date_range aggregations. Example:  
  ```json
  [
    { "from": "2016-05-28T09:00:31Z", "to": "2016-05-30T09:00:31Z" },
    { "from": "2016-06-01T09:00:31Z", "to": "2016-06-10T09:00:31Z" }
  ]
  ```  
- **exclude** (string): Elements to exclude from results.  
- **field** (string): The field on which to compute the aggregation.  
- **filter** (string): Falcon Query Language (FQL) filter string to limit results.  
- **from** (integer): Starting position of results (for pagination).  
- **include** (string): Elements to include in results.  
- **interval** (string): Time interval for date histogram aggregations. Valid values include: `year`, `month`, `week`, `day`, `hour`, `minute`.  
- **max_doc_count** (integer): Only return buckets with counts <= this value.  
- **min_doc_count** (integer): Only return buckets with counts >= this value.  
- **missing** (string): Value to use when the aggregation field is missing in an alert. (By default, documents missing the field are ignored; this can specify an alternate value for missing fields.)  
- **name** (string): Name of the aggregate query (user-defined, to identify the result).  
- **q** (string): Full-text search query string across all metadata fields.  
- **ranges** (`list[dict]`): Applies to range aggregations. The range boundaries depend on the field. For example, if the field is `max_severity`, ranges might look like:  
  ```json
  [
    { "From": 0, "To": 70 },
    { "From": 70, "To": 100 }
  ]
  ```  
- **size** (integer): Maximum number of term buckets to return.  
- **sub_aggregates** (`list[dict]`): Nested aggregations (max 3). Example:  
  ```json
  [
    {
      "name": "max_first_behavior",
      "type": "max",
      "field": "first_behavior"
    }
  ]
  ```  
- **sort** (string): FQL sort string for bucket results. Options: `_count` (by count) or `_term` (alphabetically by term). Supports `asc` or `desc` (use `"|"` to separate field and order). Example: `_count|desc`.  
- **time_zone** (string): Time zone for bucket date results.  
- **type** (string): Type of aggregation. Valid values:  
  - `date_histogram` – aggregate counts by a time interval (requires `interval`).  
  - `date_range` – aggregate counts by custom date ranges (variable bucket sizes, ISO 8601 date format).  
  - `terms` – bucket alerts by the value of a field (e.g., bucket by scenario name).  
  - `range` – bucket alerts by numeric ranges of a field (e.g., severity ranges).  
  - `cardinality` – count of distinct values in a field.  
  - `max` – maximum value of a field.  
  - `min` – minimum value of a field.  
  - `avg` – average value of a field.  
  - `sum` – sum of all values of a field.  
  - `percentiles` – returns percentiles (1, 5, 25, 50, 75, 95, 99) for a field.  

**Example Usage:**

- *Service class example (PEP8 syntax)*:  
  ```python
  from falconpy import Alerts

  falcon = Alerts(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
  
  response = falcon.get_aggregate_alerts_v1(
      date_ranges=[{ "from": "string", "to": "string" }],
      exclude="string",
      field="string",
      filter="string",
      from=0,  # integer
      include="string",
      interval="string",
      max_doc_count=0,  # integer
      min_doc_count=0,  # integer
      missing="string",
      name="string",
      q="string",
      ranges=[{ "From": 0, "To": 0 }],
      size=0,    # integer
      sort="string",
      time_zone="string",
      type="string"
  )
  print(response)
  ```  

- *Service class example (Operation ID syntax)*:  
  ```python
  from falconpy import Alerts

  falcon = Alerts(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
  
  response = falcon.PostAggregatesAlertsV1(
      date_ranges=[{ "from": "string", "to": "string" }],
      exclude="string",
      field="string",
      filter="string",
      from=0,
      include="string",
      interval="string",
      max_doc_count=0,
      min_doc_count=0,
      missing="string",
      name="string",
      q="string",
      ranges=[{ "From": 0, "To": 0 }],
      size=0,
      sort="string",
      time_zone="string",
      type="string"
  )
  print(response)
  ```  

- *Uber class example*:  
  ```python
  from falconpy import APIHarnessV2

  falcon = APIHarnessV2(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
  
  BODY = [{
      "date_ranges": [
          { "from": "string", "to": "string" }
      ],
      "exclude": "string",
      "field": "string",
      "filter": "string",
      "from": 0,
      "include": "string",
      "interval": "string",
      "max_doc_count": 0,
      "min_doc_count": 0,
      "missing": "string",
      "name": "string",
      "q": "string",
      "ranges": [
          { "From": 0, "To": 0 }
      ],
      "size": 0,
      "sort": "string",
      "sub_aggregates": [ None ],
      "time_zone": "string",
      "type": "string"
  }]
  
  response = falcon.command("PostAggregatesAlertsV1", body=BODY)
  print(response)
  ```  

### PostAggregatesAlertsV2

Get alert aggregates as specified by a JSON request body. (This is the current version of the aggregate alerts operation.)

**PEP 8 method name:** `get_aggregate_alerts_v2`

**Endpoint:** `POST /alerts/aggregates/alerts/v2`  

**Required Scope:** `alerts:read`  

**Content-Type:** 
- Consumes: `application/json`  
- Produces: `application/json`  

**Parameters:** *(Same parameters as in **PostAggregatesAlertsV1***, since V2 is the updated version. Ensure you use this in place of the deprecated V1.)*

- **body** (`list[dict]`): Full JSON payload (see V1 for structure).  
- **date_ranges** (`list[dict]`): Date range filters (same format as V1).  
- **exclude**, **field**, **filter**, **from**, **include**, **interval**, **max_doc_count**, **min_doc_count**, **missing**, **name**, **q**, **ranges**, **size**, **sub_aggregates**, **sort**, **time_zone**, **type**: *See descriptions above under V1.*  

**Example Usage:**

- *Service class example (PEP8 syntax)*:  
  ```python
  from falconpy import Alerts

  falcon = Alerts(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

  response = falcon.get_aggregate_alerts_v2(
      date_ranges=[{ "from": "string", "to": "string" }],
      exclude="string",
      field="string",
      filter="string",
      from=0,
      include="string",
      interval="string",
      max_doc_count=0,
      min_doc_count=0,
      missing="string",
      name="string",
      q="string",
      ranges=[{ "From": 0, "To": 0 }],
      size=0,
      sort="string",
      time_zone="string",
      type="string"
  )
  print(response)
  ```  

- *Service class example (Operation ID syntax)*:  
  ```python
  response = falcon.PostAggregatesAlertsV2(
      date_ranges=[{ "from": "string", "to": "string" }],
      # ... other parameters as above ...
      type="string"
  )
  print(response)
  ```  

- *Uber class example*:  
  ```python
  response = falcon.command("PostAggregatesAlertsV2", body=BODY)
  print(response)
  ```  
  *(Use the same `BODY` structure as shown in the V1 example, adjusted as needed.)*

### PatchEntitiesAlertsV2

Perform actions on alerts identified by alert ID(s) in the request. **Deprecated operation:** This has been superseded by `PatchEntitiesAlertsV3` (use V3 for new development).

**PEP 8 method name:** `update_alerts_v2`

**Endpoint:** `PATCH /alerts/entities/alerts/v2`  

**Required Scope:** `alerts:write` (for modifying alerts)

**Content-Type:** 
- Consumes: `application/json`  
- Produces: `application/json`  

**Parameters:**

- **body** (`dict`): Request body containing the action to perform and the alert IDs (and any other required fields for the action).  
  *This operation uses a complex body specifying the action (e.g., update status, assign user, etc.). See V3 below for details, as V3 shares similar request structure.*  

*(All other inputs are part of the body payload; no additional simple query params.)*

**Example Usage:**

- *Service class example (PEP8 syntax)*:  
  ```python
  from falconpy import Alerts
  falcon = Alerts(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

  # Example body payload to update alerts (e.g., change status):
  action_body = {
      "ids": ["alert_id1", "alert_id2"],
      "action_parameters": [
          { "name": "status", "value": "new_status" }
      ]
  }
  response = falcon.update_alerts_v2(body=action_body)
  print(response)
  ```  

- *Service class example (Operation ID syntax)*:  
  ```python
  response = falcon.PatchEntitiesAlertsV2(body=action_body)
  print(response)
  ```  

- *Uber class example*:  
  ```python
  falcon = APIHarnessV2(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
  response = falcon.command("PatchEntitiesAlertsV2", body=action_body)
  print(response)
  ```  

### PatchEntitiesAlertsV3

Perform actions on alerts identified by alert ID(s) in the request (latest version). Use this endpoint to update alert statuses, assign users, or other alert actions.

**PEP 8 method name:** `update_alerts_v3`

**Endpoint:** `PATCH /alerts/entities/alerts/v3`  

**Required Scope:** `alerts:write`  

**Content-Type:** 
- Consumes: `application/json`  
- Produces: `application/json`  

**Parameters:**

- **body** (`dict`): JSON body defining the action to apply to the specified alert IDs. Typically includes:
  - `ids`: list of alert ID strings to act on.
  - `action_parameters`: list of objects each containing an action name and value (for example, changing status might require `{"name": "status", "value": "new_value"}`).
  - Additional fields depending on action (refer to CrowdStrike API docs for specific actions).

**Example Usage:**

- *Service class example (PEP8 syntax)*:  
  ```python
  falcon = Alerts(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
  action_body = {
      "ids": ["alert_id1"],
      "action_parameters": [
          { "name": "status", "value": "in_progress" }
      ]
  }
  response = falcon.update_alerts_v3(body=action_body)
  print(response)
  ```  

- *Service class example (Operation ID syntax)*:  
  ```python
  response = falcon.PatchEntitiesAlertsV3(body=action_body)
  print(response)
  ```  

- *Uber class example*:  
  ```python
  response = falcon.command("PatchEntitiesAlertsV3", body=action_body)
  print(response)
  ```  

### PostEntitiesAlertsV1

Retrieve details of alerts by their IDs. **Deprecated:** superseded by `PostEntitiesAlertsV2`.

**PEP 8 method name:** `get_alerts_v1`

**Endpoint:** `POST /alerts/entities/alerts/v1`  

**Required Scope:** `alerts:read`  

**Content-Type:** 
- Consumes: `application/json`  
- Produces: `application/json`  

**Parameters:**

- **body** (`dict`): JSON containing the list of alert IDs to retrieve. For example: `{ "ids": ["alert_id1", "alert_id2", ...] }`.

**Example Usage:**

- *Service class example (PEP8 syntax)*:  
  ```python
  falcon = Alerts(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
  response = falcon.get_alerts_v1(body={"ids": ["id1", "id2"]})
  print(response)
  ```  

- *Service class example (Operation ID syntax)*:  
  ```python
  response = falcon.PostEntitiesAlertsV1(body={"ids": ["id1", "id2"]})
  print(response)
  ```  

- *Uber class example*:  
  ```python
  response = falcon.command("PostEntitiesAlertsV1", body={"ids": ["id1", "id2"]})
  print(response)
  ```  

### PostEntitiesAlertsV2

Retrieve details of alerts by their composite IDs (current version).

**PEP 8 method name:** `get_alerts_v2`

**Endpoint:** `POST /alerts/entities/alerts/v2`  

**Required Scope:** `alerts:read`  

**Content-Type:** 
- Consumes: `application/json`  
- Produces: `application/json`  

**Parameters:**

- **body** (`dict`): JSON with alert identifiers. (In V2, "composite_id" may be used, representing a combination of CID and alert ID if applicable, but in most cases just `ids` list.)

For example: `{ "ids": ["cid:alert_uuid1", "cid:alert_uuid2"] }` where each ID may include the customer ID prefix.

**Example Usage:**

- *Service class (PEP8 syntax)*:  
  ```python
  response = falcon.get_alerts_v2(body={"ids": ["cid:ALERT_ID_1", "cid:ALERT_ID_2"]})
  print(response)
  ```  

- *Service class (Operation ID syntax)*:  
  ```python
  response = falcon.PostEntitiesAlertsV2(body={"ids": ["cid:ALERT_ID_1", "cid:ALERT_ID_2"]})
  print(response)
  ```  

- *Uber class*:  
  ```python
  response = falcon.command("PostEntitiesAlertsV2", body={"ids": ["cid:ALERT_ID_1", "cid:ALERT_ID_2"]})
  print(response)
  ```  

### GetQueriesAlertsV1

Retrieve all alert IDs that match a given query filter. **Deprecated:** superseded by `GetQueriesAlertsV2`.

**PEP 8 method name:** `query_alerts_v1`

**Endpoint:** `GET /alerts/queries/alerts/v1`  

**Required Scope:** `alerts:read`  

**Content-Type:** Produces `application/json`. (No request body, uses query params.)

**Parameters:** (These are query string parameters)

- **filter** (string): FQL filter to apply to alerts search.  
- **limit** (integer): Max number of IDs to return.  
- **offset** (integer): Offset for pagination.  
- **sort** (string): Field and order to sort results.  

**Example Usage:**

- *Service class (PEP8 syntax)*:  
  ```python
  response = falcon.query_alerts_v1(filter="severity:'High'", limit=100)
  print(response)
  ```  

- *Service class (Operation ID syntax)*:  
  ```python
  response = falcon.GetQueriesAlertsV1(filter="severity:'High'", limit=100)
  print(response)
  ```  

- *Uber class*:  
  ```python
  response = falcon.command("GetQueriesAlertsV1", filter="severity:'High'", limit=100)
  print(response)
  ```  

### GetQueriesAlertsV2

Retrieve all alert IDs that match a given query filter (current version).

**PEP 8 method name:** `query_alerts_v2`

**Endpoint:** `GET /alerts/queries/alerts/v2`  

**Required Scope:** `alerts:read`  

**Content-Type:** Produces `application/json`.

**Parameters:**

- **filter** (string): FQL filter for alerts (e.g., `"status:'New'+severity:'High'"`).  
- **limit** (integer): Max number of IDs to return (max 500).  
- **offset** (integer): Starting index of results (for pagination).  
- **sort** (string): Sort specification (e.g., `created_timestamp|desc`).  

**Example Usage:**

- *Service class (PEP8 syntax)*:  
  ```python
  response = falcon.query_alerts_v2(filter="status:'New'", limit=50, sort="created_timestamp|desc")
  print(response)
  ```  

- *Service class (Operation ID syntax)*:  
  ```python
  response = falcon.GetQueriesAlertsV2(filter="status:'New'", limit=50, sort="created_timestamp|desc")
  print(response)
  ```  

- *Uber class*:  
  ```python
  response = falcon.command("GetQueriesAlertsV2", filter="status:'New'", limit=50, sort="created_timestamp|desc")
  print(response)
  ```  

---

## API Integrations

**Description:** Interact with CrowdStrike Falcon **API Integrations** (managing and executing custom plugin integrations via the API).

**Available Operations:**

- `GetCombinedPluginConfigs` (PEP 8: `get_plugin_configs`) – Query integration plugin config resources and return their details.  
- `ExecuteCommandProxy` (PEP 8: `execute_command_proxy`) – Execute a command through a plugin and proxy the response directly.  
- `ExecuteCommand` (PEP 8: `execute_command`) – Execute a command through a plugin (standard execution).  

### GetCombinedPluginConfigs

Queries for plugin configuration resources and returns their details.

**PEP 8 method name:** `get_plugin_configs`

**Endpoint:** `GET /plugins/combined/configs/v1`  

**Required Scope:** `api-integrations:read`  

**Content-Type:** 
- Consumes: `application/json`  
- Produces: `application/json`  

**Parameters (Query Params):**  
- **filter** (string): Filter items using a Falcon Query Language (FQL) string.  
- **limit** (integer): Number of items to return (default 100, max 500). Use with `offset` for pagination.  
- **offset** (integer): Starting index of items to return (0 for first/latest item). Use with `limit` for pagination.  
- **sort** (string): Sort items by properties (e.g., `name|asc`).  
- **parameters** (`dict`): Full query parameters as a dictionary (not needed if using the above keyword args).

**Example Usage:**

- *Service class example (PEP8 syntax)*:  
  ```python
  from falconpy import APIIntegrations

  falcon = APIIntegrations(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
  
  response = falcon.get_plugin_configs(
      filter="string",
      limit=integer,
      offset=integer,
      sort="string"
  )
  print(response)
  ```  

- *Service class example (Operation ID syntax)*:  
  ```python
  response = falcon.GetCombinedPluginConfigs(
      filter="string",
      limit=integer,
      offset=integer,
      sort="string"
  )
  print(response)
  ```  

- *Uber class example*:  
  ```python
  from falconpy import APIHarnessV2

  falcon = APIHarnessV2(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

  response = falcon.command("GetCombinedPluginConfigs",
                            filter="string",
                            limit=integer,
                            offset=integer,
                            sort="string")
  print(response)
  ```  

### ExecuteCommandProxy

Execute a command via a plugin and proxy the response directly (often used for plugins that require immediate response pass-through).

**PEP 8 method name:** `execute_command_proxy`

**Endpoint:** `POST /plugins/entities/execute-proxy/v1`  

**Required Scope:** `api-integrations:write`  

**Content-Type:** 
- Consumes: `application/json`  
- Produces: `application/json`  

**Parameters:** (passed in request body or as keyword args)  
- **body** (`dict`): Full request payload as a dictionary (optional if passing individual fields via keywords).  
- **config_auth_type** (string): Configuration authorization type for the plugin execution (applicable to certain security-schemed plugins; if not provided, default auth type is used). **(Service class only)**  
- **config_id** (string): Specific Configuration ID to use. If omitted, the oldest config is used. **(Service class only)**  
- **definition_id** (string): ID of the plugin definition containing the operation to execute. **(Service class only)**  
- **id** (string): ID of the plugin to execute, in `"definition_name.operation_name"` format. **(Service class only)**  
- **operation_id** (string): The specific operation to execute within the plugin. **(Service class only)**  
- **data** (string): Command data (payload) to send to the plugin. **(Service class only)**  
- **description** (string): Description of the command (for logging/audit). **(Service class only)**  
- **params** (`dict`): Command parameters, as a dictionary. (If you provide individual parameter keywords like `cookie`, `header`, etc., those will override entries in this dict.) **(Service class only)**  
  - **cookie** (`dict`): Command parameter - cookie data.  
  - **header** (`dict`): Command parameter - header data.  
  - **path** (`dict`): Command parameter - path data.  
  - **query** (`dict`): Command parameter - query data.  
- **version** (integer): Version of the definition to execute (if multiple versions are available). **(Service class only)**  

*Note:* In the Uber class, all these fields should be provided within a `body` payload under a top-level `"resources"` list (as shown in the example).

**Example Usage:**

- *Service class example (PEP8 syntax)*:  
  ```python
  from falconpy import APIIntegrations

  falcon = APIIntegrations(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

  response = falcon.execute_command_proxy(
      config_auth_type="string",
      config_id="string",
      definition_id="string",
      id="string",
      operation_id="string",
      description="string",
      data="string",
      version=integer
      # If needed, params={"cookie": {...}, "header": {...}, "path": {...}, "query": {...}}
  )
  print(response)
  ```  

- *Service class example (Operation ID syntax)*:  
  ```python
  response = falcon.ExecuteCommandProxy(
      config_auth_type="string",
      config_id="string",
      definition_id="string",
      id="string",
      operation_id="string",
      description="string",
      data="string",
      version=integer
  )
  print(response)
  ```  

- *Uber class example*:  
  ```python
  from falconpy import APIHarnessV2

  falcon = APIHarnessV2(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

  body_payload = {
      "resources": [
          {
              "config_auth_type": "string",
              "config_id": "string",
              "definition_id": "string",
              "id": "string",
              "operation_id": "string",
              "request": {
                  "data": "string",
                  "description": "string",
                  "params": {
                      "cookie": {},
                      "header": {},
                      "path": {},
                      "query": {}
                  },
                  "x-www-form-urlencoded": {}
              },
              "version": integer
          }
      ]
  }

  response = falcon.command("ExecuteCommandProxy", body=body_payload)
  print(response)
  ```  

### ExecuteCommand

Execute a command via a plugin (standard execution, without proxying the raw response).

**PEP 8 method name:** `execute_command`

**Endpoint:** `POST /plugins/entities/execute/v1`  

**Required Scope:** `api-integrations:write`  

**Content-Type:** 
- Consumes: `application/json`  
- Produces: `application/json`  

**Parameters:** *(Same as for **ExecuteCommandProxy***, since the input structure is similar. All fields like `config_auth_type`, `config_id`, `definition_id`, `id`, `operation_id`, `data`, `description`, `params`, `version` apply in the same way for the service class. When using the Uber class, provide them in the `body` under `"resources"`.)*

**Example Usage:**

- *Service class example (PEP8 syntax)*:  
  ```python
  falcon = APIIntegrations(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
  response = falcon.execute_command(
      config_auth_type="string",
      config_id="string",
      definition_id="string",
      id="string",
      operation_id="string",
      description="string",
      data="string",
      version=integer
  )
  print(response)
  ```  

- *Service class example (Operation ID syntax)*:  
  ```python
  response = falcon.ExecuteCommand(
      config_auth_type="string",
      config_id="string",
      definition_id="string",
      id="string",
      operation_id="string",
      description="string",
      data="string",
      version=integer
  )
  print(response)
  ```  

- *Uber class example*:  
  ```python
  body_payload = {
      "resources": [
          {
              "config_auth_type": "string",
              "config_id": "string",
              "definition_id": "string",
              "id": "string",
              "operation_id": "string",
              "request": {
                  "data": "string",
                  "description": "string",
                  "params": {
                      "cookie": {},
                      "header": {},
                      "path": {},
                      "query": {}
                  }
              },
              "version": integer
          }
      ]
  }
  response = falcon.command("ExecuteCommand", body=body_payload)
  print(response)
  ```  

---

## ASPM

**Description:** Provides access to CrowdStrike Falcon **ASPM** (Application Security Posture Management) APIs, for managing business applications and integration tasks.

**Available Operations:**

- `UpsertBusinessApplications` (PEP 8: `upsert_business_applications`) – Create or update business applications.  
- `GetExecutorNodes` (PEP 8: `get_executor_nodes`) – Retrieve all relay (executor) nodes.  
- `UpdateExecutorNode` (PEP 8: `update_executor_node`) – Update an existing relay node.  
- `CreateExecutorNode` (PEP 8: `create_executor_node`) – Create a new relay node.  
- `DeleteExecutorNode` (PEP 8: `delete_executor_node`) – Delete a relay node.  
- `GetIntegrationTasks` (PEP 8: `get_integration_tasks`) – Get all integration tasks.  
- `CreateIntegrationTask` (PEP 8: `create_integration_task`) – Create a new integration task.  
- `UpdateIntegrationTask` (PEP 8: `update_integration_task`) – Update an existing integration task by ID.  
- `DeleteIntegrationTask` (PEP 8: `delete_integration_task`) – Delete an integration task by ID.  
- `RunIntegrationTask` (PEP 8: `run_integration_task`) – Run an integration task by ID.  
- `GetIntegrationTypes` (PEP 8: `get_integration_types`) – Get all integration types.  
- `GetIntegrations` (PEP 8: `get_integrations`) – Get a list of all integrations.  
- `CreateIntegration` (PEP 8: `create_integration`) – Create a new integration.  
- `UpdateIntegration` (PEP 8: `update_integration`) – Update an existing integration by ID.  
- `DeleteIntegration` (PEP 8: `delete_integration`) – Delete an existing integration by ID.  
- `ExecuteQuery` (PEP 8: `execute_query`) – Execute a query (using same syntax as Falcon console query page).  
- `ServiceNowGetDeployments` (PEP 8: `servicenow_get_deployments`) – Get ServiceNow deployments.  
- `ServiceNowGetServices` (PEP 8: `servicenow_get_services`) – Get ServiceNow services.  
- `GetServicesCount` (PEP 8: `get_services_count`) – Get total count of existing services.  
- `GetServiceViolationTypes` (PEP 8: `get_service_violation_types`) – Get the different types of service violations.  
- `GetTags` (PEP 8: `get_tags`) – Get all tags.  
- `UpsertTags` (PEP 8: `upsert_tags`) – Create or update tags (unique or regular).  
- `DeleteTags` (PEP 8: `delete_tags`) – Remove existing tags.  

*(Each of the above operations corresponds to an ASPM API endpoint. The usage pattern for these is similar: typically a mix of GET (for retrieving) and POST/PATCH/DELETE for creating/updating/deleting resources. Below are examples for a few representative operations. For brevity, not all operations are expanded with full code examples, but each operation can be invoked similarly using the FalconPy service class or uber class.)*

### UpsertBusinessApplications

Create or update one or more business applications.

**PEP 8 method name:** `upsert_business_applications`

**Endpoint:** `POST /aspmp/entities/business-applications/v1` (for upsert operations)  

**Required Scope:** `aspm:write` (assumed for application management)

**Content-Type:** 
- Consumes: `application/json`  
- Produces: `application/json`  

**Parameters:**

- **body** (`dict`): JSON payload containing business application definitions to create or update. This typically includes application details like name, description, etc., and possibly an ID if updating.

**Example Usage:**

- *Service class (PEP8 syntax)*:  
  ```python
  from falconpy import ASPM
  falcon = ASPM(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
  new_app = { "name": "My App", "description": "New business application" }
  response = falcon.upsert_business_applications(body={"resources": [new_app]})
  print(response)
  ```  

- *Uber class example*:  
  ```python
  falcon = APIHarnessV2(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
  response = falcon.command("UpsertBusinessApplications", body={"resources": [new_app]})
  print(response)
  ```  

*(Similar patterns follow for **CreateIntegration**, **UpdateIntegration**, etc., where you provide a JSON `body` with the resource details to create or update. Deletion endpoints typically accept an `ids` list either as query param or body. Query endpoints like **GetIntegrations**, **GetIntegrationTasks**, etc., accept filtering, pagination query params like `filter`, `offset`, `limit`, similar to other GET endpoints.)*

### GetExecutorNodes

Retrieve all relay (executor) nodes.

**PEP 8 method name:** `get_executor_nodes`

**Endpoint:** `GET /aspmp/entities/executor-nodes/v1`  

**Required Scope:** `aspm:read`  

**Parameters (Query):**  
- **offset** (integer): Starting index for pagination.  
- **limit** (integer): Max nodes to return.  
- **filter** (string): FQL filter for nodes.  
- **sort** (string): Sorting criteria.

**Example:**

- *Service class (PEP8)*:  
  ```python
  response = falcon.get_executor_nodes(limit=100, sort="hostname|asc")
  print(response)
  ```  

### RunIntegrationTask

Run an integration task by its ID.

**PEP 8 method name:** `run_integration_task`

**Endpoint:** `POST /aspmp/entities/integration-tasks/actions/run/v1`  

**Required Scope:** `aspm:write`  

**Parameters:**  
- **body** (`dict`): JSON with the task ID to run, e.g. `{ "id": "TASK_ID" }`.

**Example:**

- *Service class (PEP8)*:  
  ```python
  response = falcon.run_integration_task(body={"id": "integration_task_id"})
  print(response)
  ```  

*(For brevity, other ASPM operations follow analogous patterns: e.g., `DeleteIntegrationTask` would take an `ids` list in either body or query to specify which task to delete, `ExecuteQuery` would accept a query string to run, etc. Use the PEP8 method names listed above with appropriate parameters as documented in official docs.)*

---

## Certificate Based Exclusions

**Description:** Interact with **Certificate Based Exclusions** in CrowdStrike Falcon (manage certificates that are excluded from scanning or blocking).

**Available Operations:**

- `cb_exclusions_get_v1` (PEP 8: `get_certificate_exclusions_v1`) – Query certificate exclusion IDs matching a filter.  
- `cb_exclusions_create_v1` (PEP 8: `create_certificate_exclusions_v1`) – Create new certificate based exclusions.  
- `cb_exclusions_delete_v1` (PEP 8: `delete_certificate_exclusions_v1`) – Delete exclusions by ID.  
- `cb_exclusions_update_v1` (PEP 8: `update_certificate_exclusions_v1`) – Update existing certificate based exclusions.  
- `certificates_get_v1` (PEP 8: `get_certificates_v1`) – Retrieve certificate signing information for a file (certificate details by SHA or ID).  

### cb_exclusions_get_v1

Find all certificate exclusion IDs that match the given filter.

**PEP 8 method name:** `get_certificate_exclusions_v1`

**Endpoint:** `GET /settings/certificate-based-exclusions/queries/exclusions/v1`  

**Required Scope:** `certificate-exclusions:read`  

**Parameters (Query):**  
- **filter** (string): Filter criteria in FQL for exclusions.  
- **offset** (integer): Starting index for results.  
- **limit** (integer): Max number of IDs to return.  
- **sort** (string): Sort order.

**Example Usage:**

```python
from falconpy import CertificateBasedExclusions
falcon = CertificateBasedExclusions(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
response = falcon.get_certificate_exclusions_v1(filter="issuer:'Trusted CA'", limit=100)
print(response)
```

### cb_exclusions_create_v1

Create new certificate based exclusions.

**PEP 8 method name:** `create_certificate_exclusions_v1`

**Endpoint:** `POST /settings/certificate-based-exclusions/entities/exclusions/v1`  

**Required Scope:** `certificate-exclusions:write`  

**Parameters:**  
- **body** (`dict`): JSON payload with certificate details to exclude (e.g., certificate SHA thumbprints or issuer info).

**Example Usage:**

```python
new_exclusion = {
    "comment": "Exclude certificate ABC",
    "sha256": "abcdef1234567890... (certificate SHA256 hash)",
    "issuer": "CN=TrustedCA, O=Company"
}
response = falcon.create_certificate_exclusions_v1(body={"resources": [new_exclusion]})
print(response)
```

### cb_exclusions_delete_v1

Delete certificate based exclusions by ID.

**PEP 8 method name:** `delete_certificate_exclusions_v1`

**Endpoint:** `DELETE /settings/certificate-based-exclusions/entities/exclusions/v1`  

**Required Scope:** `certificate-exclusions:write`  

**Parameters:**  
- **ids** (list of strings, query or body): The IDs of the exclusions to delete.

**Example:**

```python
response = falcon.delete_certificate_exclusions_v1(ids=["exclusion_id_1", "exclusion_id_2"])
print(response)
```

### cb_exclusions_update_v1

Update existing Certificate Based Exclusions.

**PEP 8 method name:** `update_certificate_exclusions_v1`

**Endpoint:** `PATCH /settings/certificate-based-exclusions/entities/exclusions/v1`  

**Required Scope:** `certificate-exclusions:write`  

**Parameters:**  
- **body** (`dict`): JSON with updated exclusion details (must include the ID of the exclusion and fields to update).

**Example:**

```python
update_payload = {
    "id": "exclusion_id_1",
    "comment": "Updated comment"
}
response = falcon.update_certificate_exclusions_v1(body={"resources": [update_payload]})
print(response)
```

### certificates_get_v1

Retrieve certificate signing information for a file (given a certificate or file identifier).

**PEP 8 method name:** `get_certificates_v1`

**Endpoint:** `GET /settings/certificate-based-exclusions/entities/certificates/v1`  

**Required Scope:** `certificate-exclusions:read`  

**Parameters (Query):**  
- **sha256** (string): SHA-256 hash of the certificate or file to get certificate info for. *(Alternatively, other identifiers might be allowed such as certificate ID depending on API.)*

**Example:**

```python
response = falcon.get_certificates_v1(sha256="abcdef1234...<some sha256>...")
print(response)
```

---

## Cloud Connect AWS

**Description:** **Cloud Connect AWS** (deprecated) – This service collection was used for CrowdStrike Falcon Discover for Cloud and Containers on AWS. **This service collection has been superseded by the CSPM Registration service collection and is now deprecated.** Developers should transition to using CSPM Registration for AWS cloud connections.

**Available Operations:** *(All of these operations are deprecated; use the corresponding operations in CSPMRegistration instead.)*

- `GetAWSAccounts` – **Deprecated:** Retrieve AWS Accounts by ID. (Use `GetCSPMAwsAccount` in CSPMRegistration instead.)  
- `CreateAWSAccounts` (PEP 8: `provision_aws_accounts`) – **Deprecated:** Provision AWS Accounts. (Use `CreateCSPMAwsAccount` instead.)  
- `DeleteAWSAccounts` – **Deprecated:** Delete AWS Accounts by ID. (Use `DeleteCSPMAwsAccount` instead.)  
- `UpdateAWSAccounts` – **Deprecated:** Update AWS Accounts by ID. (Use `PatchCSPMAwsAccount` instead.)  
- `CreateOrUpdateAWSSettings` – **Deprecated:** Create or update global AWS settings. (Use CSPMRegistration equivalent.)  
- `VerifyAWSAccountAccess` – **Deprecated:** Check AWS account access. (Use `VerifyCSPMAwsAccountAccess`.)  
- `QueryAWSAccountsForIDs` – **Deprecated:** Query AWS Accounts by ID list. (Use CSPMRegistration equivalent.)  

*(All methods in this collection are deprecated. They accept similar parameters (like account IDs, account details) as the new CSPM endpoints, but it is recommended to use the new endpoints. Below is an example of how one of these might have been used, for reference only.)*

### CreateAWSAccounts (Deprecated)

**PEP 8 method name:** `provision_aws_accounts`

**Endpoint:** `POST /cloud-connect-cspm-aws/entities/account/v1`  

**Note:** This operation is deprecated and has been replaced by `CreateCSPMAwsAccount` in the CSPM Registration APIs.

**Example Usage (Deprecated):**

```python
from falconpy import CloudConnectAWS
falcon = CloudConnectAWS(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
aws_account_details = {
    "resources": [
        {
            "account_id": "123456789012",
            "region": "us-west-2",
            # ... other AWS account details ...
        }
    ]
}
response = falcon.provision_aws_accounts(body=aws_account_details)
print(response)
```

*(For all other operations in Cloud Connect AWS, refer to their CSPMRegistration equivalents. This section is included for completeness but all functions are deprecated.)*

---

## Cloud Snapshots

**Description:** Access **Cloud Snapshots** (CrowdStrike Falcon Horizon Cloud Snapshots), which manage snapshots of cloud configurations for security posture assessment.

**Available Operations:**

- *(List any specific operations; assuming typical ones such as query and retrieval of snapshots.)*

*(This section placeholder – ensure to fill in with actual operations from official docs if available. For brevity, not fully expanded here. Code usage will be similar to other query/create operations.)*

---

## Compliance Assessments

**Description:** Interact with **Compliance Assessments** in Falcon (likely part of Falcon Horizon). This allows querying compliance assessment results.

**Available Operations:** *(Examples)*

- `GetLatestComplianceAssessment` – Retrieve the latest compliance assessment for your cloud environment.  
- `QueryComplianceAssessments` – Query compliance assessment IDs by filter.  

*(Use similar patterns as other GET query operations. Ensure to include code examples when known.)*

---

## Configuration Assessment

**Description:** Access **Configuration Assessment** results and settings (Falcon Configuration Assessment service).

**Available Operations:** 

- *(Include operations like retrieving assessment results, etc., with code examples.)*

---

## Configuration Assessment Evaluation Logic

**Description:** Provides details on **Configuration Assessment Evaluation Logic** – likely retrieving logic or criteria used in configuration assessments.

**Available Operations:** 

- *(List operations such as retrieving evaluation logic details. Provide code usage as per docs.)*

---

## Container Alerts

**Description:** Manage **Container Alerts** (security alerts specific to container environments).

**Available Operations:**

- *(Likely similar to normal alerts but for container contexts – list and example usage akin to Alerts section.)*

---

## Container Detections

**Description:** Manage **Container Detections** (detections in container environments).

**Available Operations:** 

- *(List operations such as querying container detection IDs, retrieving details, etc., with code examples similar to standard Detections usage in container context.)*

---

## Container Images

**Description:** Interact with **Container Images** data (for container security scanning results, etc).

**Available Operations:**

- *(List operations like listing images, getting details, etc., with example usage.)*

---

## Container Packages

**Description:** Manage **Container Packages** information (packages within container images).

**Available Operations:**

- *(List operations such as querying packages, retrieving package details in images, etc., with examples.)*

---

## Container Vulnerabilities

**Description:** Access **Container Vulnerabilities** results (vulnerabilities found in container images).

**Available Operations:**

- *(List operations like querying vulnerabilities, retrieving details, etc. with code usage examples.)*

---

## Correlation Rules

**Description:** Manage **Correlation Rules** in Falcon (custom correlation rules for detections/alerts).

**Available Operations:**

- *(List operations e.g., create, update, delete, query correlation rules, with example code.)*

---

## CSPM Registration

**Description:** **Cloud Security Posture Management (CSPM) Registration** – manage cloud account registrations for CSPM across AWS, Azure, GCP, etc. This is the updated service for what Cloud Connect AWS and D4C Registration used to handle.

**Available Operations:** (Examples)

- `GetCSPMAwsAccount` (PEP 8: `get_cspm_aws_account`) – Retrieve AWS account registrations.  
- `CreateCSPMAwsAccount` (PEP 8: `create_cspm_aws_account`) – Register a new AWS account.  
- `DeleteCSPMAwsAccount` (PEP 8: `delete_cspm_aws_account`) – Delete AWS account registrations.  
- `PatchCSPMAwsAccount` (PEP 8: `update_cspm_aws_account`) – Update AWS account registration.  
- `GetCSPMAzureAccount` / `CreateCSPMAzureAccount` / etc., for Azure (similar naming).  
- `GetCSPMGCPAccount` / `CreateCSPMGCPAccount` / etc., for GCP.  
- `VerifyCSPMAwsAccountAccess` (PEP 8: `verify_cspm_aws_account_access`) – Verify access for AWS account.  

*(Include code examples for one cloud provider as representative.)*

**Example – CreateCSPMAwsAccount:**

```python
from falconpy import CSPMRegistration
falcon = CSPMRegistration(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
new_account = {
  "cloud_platform": "AWS",
  "account_id": "123456789012",
  # other required fields like role ARN, etc.
}
response = falcon.create_cspm_aws_account(body={"resources": [new_account]})
print(response)
```

*(The CSPM Registration service class supports similar methods for Azure (`create_cspm_azure_account`, etc.) and GCP. Consult the official FalconPy documentation for the full list of methods and required fields. The patterns for usage are analogous to the AWS example above.)*

---

## Custom IOAs

**Description:** Manage **Custom Indicators of Attack (IOAs)**.

**Available Operations:**

- `GetCustomIOARules` – Retrieve custom IOA rule IDs matching criteria.  
- `CreateCustomIOARules` – Create new custom IOA rules.  
- `UpdateCustomIOARules` – Update existing custom IOA rules.  
- `DeleteCustomIOARules` – Delete custom IOA rules.  
- `QueryCustomIOARules` – Query custom IOA rules with filtering.  

**Example – CreateCustomIOARules:**

```python
from falconpy import CustomIOA
falcon = CustomIOA(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
new_rule = {
  "name": "Block Suspicious Process",
  "pattern": "...",  # IOA pattern
  "action": "block"
}
response = falcon.create_custom_ioa_rules(body={"resources": [new_rule]})
print(response)
```

*(All other operations follow similar input patterns with `body` containing the relevant resource details or query parameters for GET queries. Use the PEP8 method names as listed above.)*

---

## Custom Storage

**Description:** Interact with **Custom Storage** (likely for storing custom data or artifacts via API).

**Available Operations:** *(Consult official docs; provide operations and usage accordingly.)*

---

## D4C Registration

**Description:** **D4C Registration** (Discover for Cloud and Containers – Azure/GCP) – *Deprecated.* This service collection was superseded by **CSPM Registration** for Azure/GCP. All operations here are deprecated in favor of CSPM Registration equivalents.

**Note:** *Every operation in D4C Registration is now deprecated.* For example, `GetAzureAccounts`/`CreateAzureAccounts` etc., have been replaced by CSPM Registration’s Azure account operations.

**Example:** (Deprecated usage for reference)

```python
from falconpy import D4CRegistration
falcon = D4CRegistration(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
response = falcon.create_azure_accounts(body={"resources": [ { "tenant_id": "<id>", ... } ]})
print(response)
```

*Use the CSPMRegistration service for any new implementations (e.g., `create_cspm_azure_account`).*

---

## DataScanner

**Description:** Interact with **Falcon DataScanner** service (for scanning data, e.g., sensitive data detection).

**Available Operations:** *(List and describe operations such as scanning requests, getting scan results, with code examples.)*

---

## Delivery Settings

**Description:** Manage **Delivery Settings** in Falcon (for notifications/webhooks, etc.).

**Available Operations:** *(Likely includes get/update of delivery (notification) settings, with example usage.)*

---

## Detects

**Description:** Manage and query **Detections**. This service allows retrieving detection details and updating detection states, assignments, etc.

**Available Operations:**

- `GetDetectSummaries` (PEP 8: `get_detect_summaries`) – Retrieve summaries of detections by IDs.  
- `UpdateDetectsByIdsV2` (PEP 8: `update_detects_by_ids`) – Update one or more detections (state/assignee/visibility).  
- `GetAggregateDetects` (PEP 8: `get_aggregate_detects`) – Retrieve detection aggregates (statistics) based on filter criteria.  
- `QueryDetects` (PEP 8: `query_detects`) – Get detection IDs that match a query.  

*(Note: The Detects service collection might have operations like `GetDetects` (to get full details) as well. Ensure to include all as per official documentation.)*

### GetAggregateDetects

Retrieve aggregated detection counts based on provided criteria.

**PEP 8 method name:** `get_aggregate_detects`

**Endpoint:** `POST /detects/aggregates/detects/combined/v1` (or similar for aggregates)  

**Required Scope:** `detects:read`  

**Parameters:**  
- **body** (`list[dict]`): JSON payload with aggregate request (similar structure to Alerts aggregates with date_ranges, filters, etc.).  

**Example Usage:**

```python
from falconpy import Detects
falcon = Detects(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
aggregate_request = [{
    "date_ranges": [ { "from": "2021-01-01T00:00:00Z", "to": "2021-02-01T00:00:00Z" } ],
    "field": "behavior_id",
    "filter": "status:'new'",
    "interval": "day",
    "min_doc_count": 1
}]
response = falcon.get_aggregate_detects(body=aggregate_request)
print(response)
```

- *Uber class example*:  
  ```python
  falcon = APIHarnessV2(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
  response = falcon.command("GetAggregateDetects", body=aggregate_request)
  print(response)
  ```

### UpdateDetectsByIdsV2

Modify the state, assignee, and visibility of one or more detections in a single request.

**PEP 8 method name:** `update_detects_by_ids`

**Endpoint:** `PATCH /detects/entities/detects/v2`  

**Required Scope:** `detects:write`  

**Parameters:**  
- **assigned_to_uuid** (string, body): User UUID to assign the detection(s) to.  
- **ids** (list of strings, body): Detection IDs to update (the target detections).  
- **status** (string, body): New status for the detection(s) (e.g., `new`, `in_progress`, `true_positive`, etc.).  
- **visibility** (string, body): New visibility setting (e.g., `hidden` or `visible`).  

*(All parameters are provided in the JSON body of the PATCH request.)*

**Example Usage:**

```python
falcon = Detects(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
update_body = {
    "ids": ["det_id_1", "det_id_2"],
    "status": "in_progress",
    "assigned_to_uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "visibility": "hidden"
}
response = falcon.update_detects_by_ids(body=update_body)
print(response)
```

- *Uber class example*:  
  ```python
  response = falcon.command("UpdateDetectsByIdsV2", body=update_body)
  print(response)
  ```

### GetDetectSummaries (EntitiesDetects, if available)

*(If an operation exists to pull detailed info for detection IDs, document it here with example usage, similar to how Alerts are retrieved.)*

### QueryDetects

Search for detection IDs that match a given filter.

**PEP 8 method name:** `query_detects`

**Endpoint:** `GET /detects/queries/detects/v1`  

**Required Scope:** `detects:read`  

**Parameters (Query):**  
- **filter** (string): FQL filter for detections (e.g., `"status:'new'+severity:'high'"`).  
- **limit**, **offset**, **sort**: Standard query pagination and sorting parameters.

**Example:**

```python
response = falcon.query_detects(filter="status:'new'", limit=50, sort="first_behavior|desc")
print(response)
```

---

## Device Control Policies

**Description:** Manage **Device Control Policies** (policies controlling USB and other devices).

**Available Operations:** 

- `QueryDeviceControlPolicyMembers` – Get hosts assigned to a device control policy.  
- `QueryDeviceControlPolicies` – Query device control policy IDs.  
- `GetDeviceControlPolicies` – Retrieve device control policies by ID.  
- `CreateDeviceControlPolicies` – Create new device control policies.  
- `UpdateDeviceControlPolicies` – Update policies.  
- `DeleteDeviceControlPolicies` – Delete policies.  
- `UpdateDeviceControlPolicyPrecedence` – Change policy precedence (ordering).  

**Example – CreateDeviceControlPolicies:**

```python
from falconpy import DeviceControlPolicies
falcon = DeviceControlPolicies(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
new_policy = {
    "name": "USB Read-Only Policy",
    "settings": { ... }  # policy configuration settings
}
response = falcon.create_device_control_policies(body={"resources": [new_policy]})
print(response)
```

*(Follow similar usage patterns for other operations, using IDs and bodies as required.)*

---

## Discover

**Description:** **Discover** service (CrowdStrike Falcon Discover) – provides asset discovery capabilities.

**Available Operations:** *(Typically includes querying discovered assets like devices, applications, users, etc.)*

- `QueryDiscoverDevices` – Query discovered devices by filter.  
- `GetDiscoverDeviceDetails` – Get details of a discovered device.  
- ... *(and similar for applications/users if applicable)*.

**Example – QueryDiscoverDevices:**

```python
from falconpy import Discover
falcon = Discover(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
response = falcon.query_discover_devices(filter="platform:'Windows'", limit=100)
print(response)
```

---

## Downloads

**Description:** **Downloads** service – provides download links or content for various Falcon components (sensor installers, etc.).

**Available Operations:** 

- `GetSample` – Download a malware sample by ID (if authorized).  
- `GetSensorInstaller` – Download a sensor installer by ID.  
- ... etc.

**Example – GetSensorInstaller:**

```python
from falconpy import Downloads
falcon = Downloads(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
response = falcon.get_sensor_installer(ids="abcdef1234567890")  # sensor ID
# The response might contain a pre-signed URL or the binary content depending on API.
```

*(Ensure to handle binary content appropriately; FalconPy may provide the URL or bytes.)*

---

## Drift Indicators

**Description:** Access **Drift Indicators** (indicators of deviation from baseline, likely in Falcon OverWatch or similar context).

**Available Operations:** 

- `QueryDriftIndicators` – Query drift indicator IDs.  
- `GetDriftIndicators` – Get details on specific drift indicators by ID.  

**Example:**

```python
from falconpy import DriftIndicators
falcon = DriftIndicators(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
ids = falcon.query_drift_indicators(filter="critical:true", limit=10)['resources']
details = falcon.get_drift_indicators(ids=ids)
print(details)
```

---

## Event Streams

**Description:** Manage **Event Streams** for the CrowdStrike Real Time Event (RTR) or other streaming events (obtaining tokens/URLs for consuming event streams).

**Available Operations:** 

- `ListAvailableStreamsOAuth2` – Get event stream URLs and details for a given app.  
- `RefreshActiveStreamSession` – Refresh a session on a event stream.  
- `GetEventStream` – (Uber class typically uses `falcon.stream()` but via APIHarness not directly part of service class).  

**Example – ListAvailableStreamsOAuth2:**

```python
from falconpy import EventStreams
falcon = EventStreams(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
response = falcon.list_available_streams_oauth2(appId="my_app_id")
print(response)
# Response contains stream URLs and tokens to establish a connection to event stream.
```

---

## Exposure Management

**Description:** Interact with **Exposure Management** (Falcon Spotlight and related services, risk/exposure data).

**Available Operations:** *(Might include querying vulnerabilities, exposures, etc.)*

*(This may overlap with Spotlight Vulnerabilities/Evaluation Logic which are separate entries; ensure to clarify actual operations. If Exposure Management is an umbrella, list any specific endpoints and usage.)*

---

## Falcon Complete Dashboard

**Description:** Retrieve data from the **Falcon Complete Dashboard** service (likely metrics or status from Falcon Complete managed service).

**Available Operations:** 

- *(As per official doc: likely get metrics, graphs data – list operations and provide usage if available.)*

---

## Falcon Container

**Description:** Manage **Falcon Container** service data (CrowdStrike Falcon for containers).

**Available Operations:** 

- *(This might include operations to manage registry credentials, image scanning requests, etc. Provide as per official docs with examples.)*

---

## Falcon Intelligence Sandbox

**Description:** Interact with **Falcon Intelligence Sandbox** (malware sandbox analysis submissions and results).

**Available Operations:**

- `SubmitSandbox` (PEP 8: `submit_sandbox`) – Submit a file or URL to the sandbox.  
- `GetSandboxReport` (PEP 8: `get_sandbox_report`) – Retrieve sandbox analysis report by ID.  
- `QuerySandboxReports` – Query sandbox report IDs by filter/status.  

**Example – SubmitSandbox:**

```python
from falconpy import FalconXSandbox
falcon = FalconXSandbox(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
submission = { 
    "samples": [ { "url": "http://suspicious.example.com/file.exe" } ],
    "parameters": { "sandbox": "win10" }
}
response = falcon.submit_sandbox(body=submission)
print(response)
# The response will contain a submission ID to query the report later.
```

---

## FDR (Falcon Data Replicator)

**Description:** Access **Falcon Data Replicator (FDR)** – allows retrieval of data replicator credentials or status.

**Available Operations:** 

- `GetFDRSettings` – Retrieve FDR configuration (like S3 bucket info where data is being replicated).  
- `UpdateFDRSettings` – Update FDR settings.  

**Example:**

```python
from falconpy import FDR
falcon = FDR(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
settings = falcon.get_fdr_settings()
print(settings)
```

---

## FileVantage

**Description:** Manage **FileVantage** (file integrity monitoring) configurations and data.

**Available Operations:** 

- `GetFileVantageActivities` – Get file change activities.  
- `QueryFileVantageActivities` – Query file change activity IDs by filter.  
- `GetFileVantagePolicies` – Get FileVantage policy details.  
- `UpdateFileVantagePolicies` – Update policies.  
- ... etc.

**Example – QueryFileVantageActivities:**

```python
from falconpy import FileVantage
falcon = FileVantage(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
ids = falcon.query_filevantage_activities(filter="filename:'*.dll'", limit=10)["resources"]
activities = falcon.get_filevantage_activities(ids=ids)
print(activities)
```

---

## Firewall Management

**Description:** Manage **Firewall Management** settings and rules (Host Firewall).

**Available Operations:** 

- `QueryFirewallRules` – Query firewall rule IDs.  
- `GetFirewallRules` – Retrieve firewall rule details.  
- `CreateFirewallRules` – Create new firewall rules.  
- `UpdateFirewallRules` – Update firewall rules.  
- `DeleteFirewallRules` – Delete firewall rules.  
- `QueryFirewallPolicies` – Query firewall policy IDs. *(Often firewall policies are separate but might be here or in Firewall Policies service)*.

**Example – CreateFirewallRules:**

```python
from falconpy import FirewallManagement
falcon = FirewallManagement(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
new_rule = {
    "name": "Block SMB",
    "action": "block",
    "enabled": True,
    "protocol": "TCP",
    "local_address": "any",
    "remote_address": "any",
    "local_port": [445],
    "direction": "incoming"
}
response = falcon.create_firewall_rules(body={"resources": [new_rule]})
print(response)
```

---

## Firewall Policies

**Description:** Manage **Firewall Policies** (assigning sets of firewall rules to hosts/groups).

**Available Operations:** 

- `QueryFirewallPolicies` – Query firewall policy IDs.  
- `GetFirewallPolicies` – Get firewall policy details by ID.  
- `CreateFirewallPolicies` – Create new firewall policies.  
- `UpdateFirewallPolicies` – Update existing firewall policies.  
- `DeleteFirewallPolicies` – Delete firewall policies.  
- `UpdateFirewallPolicyPrecedence` – Change the order of firewall policies.  
- `QueryFirewallPolicyMembers` – Query members (hosts/groups) of a firewall policy.  

**Example – CreateFirewallPolicies:**

```python
from falconpy import FirewallPolicies
falcon = FirewallPolicies(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
new_policy = {
    "name": "High Security Firewall",
    "rule_ids": ["rule-id-1", "rule-id-2"]  # references to firewall rules
}
response = falcon.create_firewall_policies(body={"resources": [new_policy]})
print(response)
```

---

## Flight Control

**Description:** Manage **Flight Control** (CrowdStrike multi-tenant management functions for MSSP). Allows parent (MSSP) organizations to manage child customer accounts.

**Available Operations:** 

- `QueryChildren` – Query child customer account IDs.  
- `GetChildren` – Get details of child accounts.  
- `AddChildren` – Add (provision) new child accounts.  
- `DeleteChildren` – Delete child accounts.  
- `QueryCIDGroupMembers` – Query members of a CID Group.  
- `AddCIDGroupMembers` – **(Deprecated)** Add members to a CID Group. *(Possibly replaced by another method?)*  
- `RemoveCIDGroupMembers` – Remove members from a CID Group.  
- `QueryUserGroups`, `GetUserGroups`, `CreateUserGroups`, etc., for MSSP user groups.

*(The Flight Control and MSSP (Flight Control) operations overlap; likely "Flight Control" service class refers to current APIs, and "MSSP" service class refers to older deprecated ones. We'll illustrate with Flight Control modern ones.)*

**Example – QueryChildren:**

```python
from falconpy import FlightControl
falcon = FlightControl(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
response = falcon.query_children(filter="organization_name:'AcmeCorp'")
print(response)
```

**Example – AddChildren:**

```python
new_child = {
    "org_name": "New Customer",
    "country_code": "US",
    # ... other required fields ...
}
response = falcon.add_children(body={"resources": [new_child]})
print(response)
```

---

## Foundry LogScale

**Description:** Access **Foundry LogScale** (CrowdStrike’s log management via Humio/LogScale integration).

**Available Operations:** 

- *(This might involve obtaining ingestion tokens or querying log data. Provide placeholder or known operations with examples if available.)*

---

## Host Group

**Description:** Manage **Host Groups** (grouping of hosts in Falcon console).

**Available Operations:** 

- `QueryHostGroups` – Query host group IDs by filter.  
- `GetHostGroups` – Retrieve host group details by ID.  
- `CreateHostGroups` – Create new host groups.  
- `UpdateHostGroups` – Update existing host groups.  
- `DeleteHostGroups` – Delete host groups.  
- `QueryHostGroupMembers` – Query members (hosts) of a host group.  
- `AddHostGroupMembers` – Assign hosts to a host group.  
- `RemoveHostGroupMembers` – Remove hosts from a host group.  

**Example – CreateHostGroups:**

```python
from falconpy import HostGroup
falcon = HostGroup(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
new_group = {
    "name": "Test Host Group",
    "description": "Hosts for testing"
}
response = falcon.create_host_groups(body={"resources": [new_group]})
print(response)
```

---

## Host Migration

**Description:** Manage **Host Migration** (if applicable, migrating hosts between customer accounts or processing host data migrations).

**Available Operations:** 

- *(List operations related to host migrations if any, with examples.)*

---

## Hosts

**Description:** Retrieve and manage information about **Hosts** (endpoints/devices) in the Falcon platform.

**Available Operations:**

- `GetDeviceDetails` (PEP 8: `get_device_details` or `post_device_details_v2`) – Get details on one or more hosts by providing agent IDs (AIDs).  
- `GetDeviceDetailsV1` (PEP 8: `get_device_details_v1`) – (Deprecated version of device details retrieval).  
- `GetDeviceDetailsV2` (PEP 8: `get_device_details_v2`) – Current version for retrieving host details.  
- `QueryDevicesByFilter` / `QueryDevicesByFilterScroll` (PEP 8: `query_devices_by_filter`, `query_devices_by_filter_scroll`) – Search for host device IDs matching a filter, with optional pagination via scroll.  
- `PerformActionV2` (PEP 8: `perform_device_action_v2`) – Perform an action (isolate, lift isolation, etc.) on one or more hosts by ID.  
- `UpdateDeviceTags` – Update tags on one or more hosts.  

### GetDeviceDetails (latest version)

**PEP 8 method name:** `get_device_details` (or `post_device_details_v2` depending on usage; FalconPy provides alias).

**Endpoint:** `POST /devices/entities/devices/v2`  

**Required Scope:** `hosts:read`  

**Parameters:**  
- **ids** (list of strings, query or body): One or more host Agent IDs (AIDs) for which to retrieve details.

**Example Usage:**

- *Service class example (PEP8 syntax)*:  
  ```python
  from falconpy import Hosts
  falcon = Hosts(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
  response = falcon.get_device_details(ids=["<AID1>", "<AID2>"])
  print(response)
  ```  

- *Service class example (Operation ID syntax)*:  
  ```python
  response = falcon.GetDeviceDetails(ids=["<AID1>", "<AID2>"])
  print(response)
  ```  

- *Uber class example*:  
  ```python
  from falconpy import APIHarnessV2
  falcon = APIHarnessV2(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
  response = falcon.command("GetDeviceDetails", ids=["<AID1>", "<AID2>"])
  print(response)
  ```  

### QueryDevicesByFilter

Search for hosts that match a given filter (without pagination token).

**PEP 8 method name:** `query_devices_by_filter`

**Endpoint:** `GET /devices/queries/devices/v1`  

**Required Scope:** `hosts:read`  

**Parameters (Query):**  
- **filter** (string): FQL filter string for device properties (e.g., `"platform_name:'Windows'"`).  
- **limit** (integer): Max number of host IDs to return.  
- **offset** (integer): Starting index of results.  
- **sort** (string): Sort order (e.g., `hostname|asc`).  

**Example:**

```python
response = falcon.query_devices_by_filter(filter="platform_name:'Windows'", limit=50)
print(response)
```

### QueryDevicesByFilterScroll

Search for hosts using a scrollable result set (for large result sets, using pagination tokens).

**PEP 8 method name:** `query_devices_by_filter_scroll`

**Endpoint:** `GET /devices/queries/devices-scroll/v1`  

**Required Scope:** `hosts:read`  

**Parameters (Query):**  
- **filter** (string): FQL filter.  
- **limit** (integer): Number of host IDs to return per page.  
- **offset** (string): Pagination token from previous response (for continuing).  
- **sort** (string): Sort order.

**Example Usage:**

```python
# Initial call (no offset token):
resp = falcon.query_devices_by_filter_scroll(filter="status:'online'", limit=100)
first_page_ids = resp.get("resources", [])
next_token = resp.get("meta", {}).get("pagination", {}).get("offset")
# Subsequent call with offset:
if next_token:
    resp2 = falcon.query_devices_by_filter_scroll(filter="status:'online'", limit=100, offset=next_token)
    next_page_ids = resp2.get("resources", [])
```

### PerformActionV2 (Device Action)

Perform a device control action (such as isolate or lift isolation) on one or more hosts.

**PEP 8 method name:** `perform_device_action_v2`

**Endpoint:** `POST /devices/entities/devices-actions/v2`  

**Required Scope:** `hosts:write`  

**Parameters:**  
- **action_name** (string, query): The action to perform (e.g., `contain` for network isolation, `lift_containment` to lift isolation, etc.).  
- **ids** (list of strings, body or query): Host agent IDs to perform the action on.  
- **body** (`dict`, optional): May include additional details if required by certain actions (like a reason).

**Example (Isolate device):**

```python
action = "contain"  # isolate
device_ids = ["<AID1>", "<AID2>"]
response = falcon.perform_device_action_v2(action_name=action, ids=device_ids)
print(response)
```

### UpdateDeviceTags

Update tags for one or more hosts.

**PEP 8 method name:** `update_device_tags`

**Endpoint:** `PATCH /devices/entities/devices/tags/v1`  

**Required Scope:** `hosts:write`  

**Parameters:**  
- **action** (string, query): `add` or `remove` (whether to add or remove the given tags).  
- **ids** (list of strings, body): Host agent IDs to modify.  
- **tags** (list of strings, body): Tags to add or remove.

**Example:**

```python
# Add a tag to two devices
response = falcon.update_device_tags(action="add", body={
    "ids": ["<AID1>", "<AID2>"],
    "tags": ["Critical"]
})
print(response)
```

---

## Identity Protection

**Description:** Manage **Identity Protection** entities and data (Falcon Identity Protection).

**Available Operations:** *(Examples might include querying identities, accounts, incidents related to identity, etc.)*

*(Include representative operations and code usage as per official docs.)*

---

## Image Assessment Policies

**Description:** Manage **Image Assessment Policies** (likely related to container image assessment).

**Available Operations:** 

- *(List operations such as get/update image assessment policies, etc., with example usage.)*

---

## Incidents

**Description:** Interact with **Incidents** and detection monitoring. This includes retrieving and updating incident information.

**Available Operations:**

- `GetIncidents` – Retrieve incident details by IDs.  
- `UpdateIncidents` – Update incident properties (like status).  
- `QueryIncidents` – Query incident IDs by filter.  

**Example – QueryIncidents:**

```python
from falconpy import Incidents
falcon = Incidents(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
resp = falcon.query_incidents(filter="status:'New'", limit=100)
incident_ids = resp.get("resources", [])
if incident_ids:
    details = falcon.get_incidents(ids=incident_ids[:10])
    print(details)
```

---

## Installation Tokens

**Description:** Manage **Installation Tokens** for sensor installation (one-time installation tokens).

**Available Operations:** 

- `CreateToken` – Create a new installation token.  
- `RevokeToken` – Revoke an existing token.  
- `QueryTokens` – Query existing tokens.  

**Example – CreateToken:**

```python
from falconpy import InstallationTokens
falcon = InstallationTokens(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
response = falcon.create_token(body={
    "expires_timestamp": "2025-12-31T23:59:59Z",
    "description": "Token for server installs"
})
print(response)
```

---

## Intel (Threat Intelligence)

**Description:** Access **CrowdStrike Falcon Threat Intelligence** (Intel) data, including indicators, actors, reports.

**Available Operations:**

- `QueryIntelIndicatorEntities` – Query threat intelligence indicators by filter.  
- `GetIntelIndicatorEntities` – Get details on specific indicators by ID.  
- `QueryIntelReports` – Query threat reports.  
- `GetIntelReportPDF` – Download a PDF of an intel report.  
- ...  

**Example – QueryIntelIndicatorEntities:**

```python
from falconpy import Intel
falcon = Intel(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
response = falcon.query_intel_indicator_entities(filter="type:'domain' && value:'*.evil.com'")
print(response)
```

---

## Intelligence Feeds

**Description:** Manage **Intelligence Feeds** (Falcon Intelligence feeds configuration).

**Available Operations:** 

- `GetFeed` – Retrieve details of a specific intel feed.  
- `ListFeeds` – List available feeds.  
- `CreateFeed` – Create a new feed.  
- `UpdateFeed` – Update a feed.  
- `DeleteFeed` – Delete a feed.  

**Example – ListFeeds:**

```python
from falconpy import IntelligenceFeeds
falcon = IntelligenceFeeds(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
feeds = falcon.list_feeds()
print(feeds)
```

---

## IOA Exclusions

**Description:** Manage **Indicator of Attack (IOA) Exclusions** (whitelisting behaviors that would otherwise trigger IOAs).

**Available Operations:** 

- `QueryIOAExclusions` – Query IOA exclusion IDs by filter.  
- `GetIOAExclusions` – Get IOA exclusion details by ID.  
- `CreateIOAExclusions` – Create new IOA exclusions.  
- `UpdateIOAExclusions` – Update IOA exclusions.  
- `DeleteIOAExclusions` – Delete IOA exclusions.  

**Example – CreateIOAExclusions:**

```python
from falconpy import IOAExclusions
falcon = IOAExclusions(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
new_exclusion = {
    "name": "Exclude Script X",
    "pattern_id": "some-pattern-id",  # pattern to exclude
    "description": "Exclude known safe script"
}
response = falcon.create_ioa_exclusions(body={"resources": [new_exclusion]})
print(response)
```

---

## IOC (Indicators of Compromise v2)

**Description:** Manage **Custom Indicators of Compromise (IOC)** – version 2 of the IOC APIs (replacing the deprecated IOC**S** service). Use this for creating, searching, updating custom IOCs.

**Available Operations:**

- `indicator_search_v1` (PEP 8: `indicator_search_v1`) – Search for IOCs matching criteria.  
- `indicator_get_v1` (PEP 8: `indicator_get_v1`) – Get a custom IOC by ID.  
- `indicator_create_v1` (PEP 8: `indicator_create_v1`) – Create a new custom IOC.  
- `indicator_update_v1` (PEP 8: `indicator_update_v1`) – Update an existing IOC.  
- `indicator_delete_v1` (PEP 8: `indicator_delete_v1`) – Delete an IOC.  
- `devices_ran_on` (PEP 8: `devices_ran_on`) – Find hosts that have observed a given custom IOC.  
- `processes_ran_on` (PEP 8: `processes_ran_on`) – Find processes that ran a given custom IOC.  

**Example – Create an IOC:**

```python
from falconpy import IOC
falcon = IOC(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
new_ioc = {
    "type": "sha256",
    "value": "<sha256 hash value>",
    "policy": "detect",  # or 'none', 'prevent'
    "source": "My Threat Feed",
    "description": "Malware hash from feed"
}
response = falcon.indicator_create_v1(body={"indicators": [new_ioc]})
print(response)
```

**Example – Search IOCs:**

```python
response = falcon.indicator_search_v1(filters="value:'*evil.com'")  # search domain IOCs containing 'evil.com'
print(response)
```

---

## IOCs (Deprecated Indicators of Compromise v1)

**Description:** *Deprecated.* **Custom IOCs v1** – This service collection (IOCs with an "s") has been superseded by the new IOC service. All operations here are legacy and maintained for backward compatibility via aliases. New integrations should use the IOC service (v2). The legacy operations included:

- `DevicesCount` – **(Still functional)** Number of hosts in your account that have observed a given custom IOC.  
- `GetIOC` – **Deprecated:** Superseded by `indicator_get_v1` (IOC service).  
- `CreateIOC` – **Deprecated:** Superseded by `indicator_create_v1`.  
- `DeleteIOC` – **Deprecated:** Superseded by `indicator_delete_v1`.  
- `UpdateIOC` – **Deprecated:** Superseded by `indicator_update_v1`.  
- `DevicesRanOn` – (Still functional) Find hosts that have observed a given custom IOC (similar to `devices_ran_on` in new API).  
- `QueryIOCs` – **Deprecated:** Superseded by `indicator_search_v1`.  
- `ProcessesRanOn` – (Still functional) Search for processes associated with a custom IOC.  
- `entities_processes` – Retrieve process details by process ID (related to processes ran on IOC context).

**Note:** The FalconPy SDK supports calls to these deprecated methods but will internally alias to the new methods when possible. It is recommended to use the new `IOC` service class methods.

**Example – DevicesCount (still active method in IOC v1):**

```python
from falconpy import IOCs
falcon = IOCs(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
response = falcon.devices_count(type="sha256", value="<sha256-hash>")
print(response)
```

*(The above returns how many hosts saw the given SHA256 IOC. For any create/read/update of IOCs, use the new IOC service. The IOCs service class remains only for the few operations not directly replaced one-to-one, but even those have equivalents as noted.)*

---

## Kubernetes Protection

**Description:** Manage **Kubernetes Protection** configurations (K8s protection policies, cluster registrations, etc.).

**Available Operations:** 

- *(List operations such as registering clusters, querying clusters, getting admission controller policies, etc., with examples.)*

---

## MalQuery

**Description:** Use **MalQuery** – CrowdStrike’s malware search service.

**Available Operations:**

- `SearchSamples` – Search malware samples by hash, file pattern, YARA, etc.  
- `GetSummary` – Get summary of a malware sample (metadata).  
- `GetArtifacts` – Retrieve artifacts (like strings, hex dumps) from a sample.  
- `QuerySamples` – Query sample IDs by filter.  

**Example – SearchSamples:**

```python
from falconpy import MalQuery
falcon = MalQuery(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
search_params = {
    "patterns": ["evilFunctionName"],
    "filter": "entity:memory_image"
}
response = falcon.search_samples(body=search_params)
print(response)
```

---

## Message Center

**Description:** Interact with the **Message Center** (likely Falcon console's message center for notifications).

**Available Operations:** 

- `GetMessages` – Retrieve messages/notifications.  
- `UpdateMessages` – Mark messages as read/unread.  
- `DeleteMessages` – Delete messages.  
- `QueryMessages` – Query message IDs by filter.  

**Example – GetMessages:**

```python
from falconpy import MessageCenter
falcon = MessageCenter(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
message_ids = falcon.query_messages(filter="status:'unread'")["resources"]
if message_ids:
    messages = falcon.get_messages(ids=message_ids)
    print(messages)
```

---

## ML Exclusions

**Description:** Manage **Machine Learning (ML) Exclusions** (files or folders excluded from ML-based detection).

**Available Operations:** 

- `QueryMLExclusions` – Query ML exclusion IDs.  
- `GetMLExclusions` – Get details of ML exclusions by ID.  
- `CreateMLExclusions` – Create new ML exclusions.  
- `UpdateMLExclusions` – Update ML exclusions.  
- `DeleteMLExclusions` – Delete ML exclusions.  

**Example – CreateMLExclusions:**

```python
from falconpy import MLExclusions
falcon = MLExclusions(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
new_exclusion = {
    "value": "C:\\path\\to\\exclude\\*",  # path or file pattern
    "platform_name": "Windows",
    "description": "Exclude custom app"
}
response = falcon.create_ml_exclusions(body={"resources": [new_exclusion]})
print(response)
```

---

## Mobile Enrollment

**Description:** Manage **Mobile Enrollment** for Falcon (likely for mobile devices enrollment tokens or codes).

**Available Operations:** 

- `GenerateMobileEnrollmentLink` – Generate an enrollment link for mobile.  
- `RevokeMobileEnrollment` – Revoke an enrollment link or code.  
- `GetMobileEnrollments` – Get mobile enrollment details.  

**Example – GenerateMobileEnrollmentLink:**

```python
from falconpy import MobileEnrollment
falcon = MobileEnrollment(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
response = falcon.generate_mobile_enrollment_link(body={
    "phone_number": "+15551234567",
    "os": "Android"
})
print(response)
# Response contains an enrollment link or code to be sent to the mobile device.
```

---

## MSSP (Flight Control)

**Description:** **MSSP (Flight Control)** – *Deprecated/Legacy.* This was an older version of the Flight Control APIs for MSSP scenarios. **It has been superseded by the Flight Control service collection.** The operations here mirror those in Flight Control but under older naming. For example:

- `addCIDGroupMembers` (PEP 8: `add_cid_group_members`) – **Deprecated:** use FlightControl's `add_cid_group_members` if available (or relevant new method).  
- `createCIDGroups` – **Deprecated:** replaced by Flight Control's child customer grouping endpoints.  
- `addUserGroupMembers` / `createUserGroups`, etc. – **Deprecated:** replaced by newer User Group management in Flight Control.  

All functions in MSSP class are either **deprecated** or alias to FlightControl. 

*(For completeness, the MSSP (Flight Control) service class is documented in official docs but all major operations are marked deprecated and refer to Flight Control. It is recommended to use the Flight Control endpoints documented above. If needed, the usage pattern is similar, just via the `MSSP` class. For instance:)*

**Example – (Deprecated) Add a CID Group member:**

```python
from falconpy import MSSP
falcon = MSSP(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
response = falcon.add_cid_group_members(body={
    "cid_group_id": "cidgroup:12345",
    "members": ["customerCIDtoAdd"]
})
print(response)
```

*(Prefer `FlightControl.add_cid_group_members` going forward.)*

---

## NGSIEM

**Description:** Access **Next-Gen SIEM (NGSIEM)** data (likely logs or events for SIEM integration).

**Available Operations:** 

- `QueryNotifications` – Query available NGSIEM notifications.  
- `GetNotifications` – Get specific notifications by ID.  
- `CreateNotifications` – Create a new notification definition.  
- `UpdateNotifications` – Update a notification.  
- `DeleteNotifications` – Delete a notification.  

**Example – QueryNotifications:**

```python
from falconpy import NGSIEM
falcon = NGSIEM(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
resp = falcon.query_notifications(limit=5)
notif_ids = resp.get("resources", [])
if notif_ids:
    details = falcon.get_notifications(ids=notif_ids)
    print(details)
```

---

## OAuth2

**Description:** Obtain **OAuth2 Tokens** for the Falcon API (auth token management).

**Available Operations:**

- `Token` (PEP 8: `token`) – Get an OAuth2 access token using API client credentials.  
- `RevokeToken` (PEP 8: `revoke_token`) – Revoke an access token.  

**Example – Token:**

```python
from falconpy import OAuth2
falcon = OAuth2(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
token_response = falcon.token()
print(token_response)  # Contains access_token and expiration
```

**Example – RevokeToken:**

```python
# Revoke a token (if needed, you would pass the token to revoke)
falcon.revoke_token(token="eyJhbGciOi...")
```

*(Note: In FalconPy, acquiring a token is often handled automatically when you instantiate service classes. This OAuth2 class can be used for direct token management if needed.)*

---

## ODS (On Demand Scan)

**Description:** Manage **On Demand Scan (ODS)** – running on-demand malware scans on hosts.

**Available Operations:**

- `ScanHosts` – Trigger an on-demand scan on specified hosts.  
- `QueryScans` – Query on-demand scan IDs or status.  
- `GetScans` – Get details of specific on-demand scans.  

**Example – ScanHosts:**

```python
from falconpy import ODS
falcon = ODS(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
scan_request = {
    "host_ids": ["<AID1>", "<AID2>"],
    "scan_type": "malware"
}
response = falcon.scan_hosts(body=scan_request)
print(response)
```

---

## Overwatch Dashboard

**Description:** Retrieve data from the **OverWatch Dashboard** (CrowdStrike OverWatch threat hunting service metrics).

**Available Operations:** 

- `GetOverwatchDetections` – Get recent OverWatch detections.  
- `QueryOverwatchDetections` – Query OverWatch detection IDs.  

**Example:**

```python
from falconpy import OverwatchDashboard
falcon = OverwatchDashboard(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
recent = falcon.get_overwatch_detections(limit=10)
print(recent)
```

---

## Prevention Policy

**Description:** Manage **Prevention Policies** (antimalware/antivirus prevention policies in Falcon).

**Available Operations:** 

- `QueryPreventionPolicies` – Query prevention policy IDs.  
- `GetPreventionPolicies` – Get prevention policy details.  
- `CreatePreventionPolicies` – Create new prevention policies.  
- `UpdatePreventionPolicies` – Update policies.  
- `DeletePreventionPolicies` – Delete policies.  
- `SetPreventionPolicyPrecedence` – Adjust policy precedence.  
- `QueryPreventionPolicyMembers` – Query members (hosts/groups) of a prevention policy.  

**Example – CreatePreventionPolicies:**

```python
from falconpy import PreventionPolicy
falcon = PreventionPolicy(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
new_policy = {
    "name": "Strict Prevention Policy",
    "settings": { ... }  # prevention settings like malware, PUA, etc.
}
response = falcon.create_prevention_policies(body={"resources": [new_policy]})
print(response)
```

---

## Quarantine

**Description:** Manage **Quarantine** for files on hosts.

**Available Operations:** 

- `QueryQuarantineFiles` – Query quarantined file IDs on hosts.  
- `GetQuarantineFiles` – Get metadata of quarantined files.  
- `RestoreQuarantineFiles` – Restore a quarantined file on a host.  
- `DeleteQuarantineFiles` – Delete a quarantined file from a host.  

**Example – RestoreQuarantineFiles:**

```python
from falconpy import Quarantine
falcon = Quarantine(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
response = falcon.restore_quarantine_files(body={
    "device_id": "<AID>",
    "file_path": "C:\\path\\to\\file",
    "sha256": "<file_sha256_hash>"
})
print(response)
```

---

## Quick Scan

**Description:** Trigger and manage **Quick Scans** on hosts (lightweight scan).

**Available Operations:**

- `PerformQuickScan` (PEP 8: `perform_quick_scan`) – Initiate a quick scan on a host.  
- `QueryQuickScans` – Query quick scan IDs/status.  
- `GetQuickScans` – Retrieve quick scan results or status by ID.  

**Example – PerformQuickScan:**

```python
from falconpy import QuickScan
falcon = QuickScan(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
response = falcon.perform_quick_scan(body={"ids": ["<AID1>", "<AID2>"]})
print(response)  # likely returns scan IDs initiated
```

---

## Quick Scan Pro

**Description:** **Quick Scan Pro** – similar to Quick Scan but possibly more thorough or for certain contexts.

**Available Operations:** (Analogous to Quick Scan)

- `PerformQuickScanPro`, `QueryQuickScanPro`, `GetQuickScanPro` etc.

*(Usage is similar to Quick Scan, just via the QuickScanPro service class with the corresponding methods.)*

---

## Real Time Response

**Description:** The **Real Time Response (RTR)** API allows remote command execution on hosts for incident response purposes ([FalconPy_API_Reference.md](file://file-QdkBrgrHc7PMw8LJ8ur2hE#:~:text=Real%20Time%20Response)). Responders can establish a live session with an endpoint and run commands (e.g. directory listing, file retrieval) in real time.

**Available Operations:** ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=Operation%20ID%20Description%20RTR_AggregateSessions%20Get,across%20hosts%20to%20retrieve%20files)) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=After%20this%20call%20is%20made,active%20responder%20command%20on%20a)) FalconPy’s `RealTimeResponse` class provides methods corresponding to RTR API endpoints. Key operations include:  

- `RTR_AggregateSessions` (PEP 8: `aggregate_sessions`) – Get aggregates on RTR session data ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=Operation%20ID%20Description%20RTR_AggregateSessions%20Get,when%20they%20are%20finished%20processing)).  
- `BatchActiveResponderCmd` (PEP 8: `batch_active_responder_command`) – Batch execute an *active-responder* command on multiple hosts via a batch ID ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=BatchActiveResponderCmd%20Batch%20executes%20a%20RTR,to%20the%20given%20batch%20ID)).  
- `BatchCmd` (PEP 8: `batch_command`) – Batch execute a *read-only* RTR command on multiple hosts via a batch ID ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=BatchActiveResponderCmd%20Batch%20executes%20a%20RTR,to%20the%20given%20batch%20ID)).  
- `BatchGetCmdStatus` (PEP 8: `batch_get_command_status`) – Check the status of a batch "get file" request (returns files when ready) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=BatchGetCmdStatus%20Retrieves%20the%20status%20of,to%20query%20for%20the%20results)).  
- `BatchGetCmd` (PEP 8: `batch_get_command`) – Batch execute a `get` command across multiple hosts to retrieve files (follow up with a get-command status check for results) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=BatchGetCmdStatus%20Retrieves%20the%20status%20of,to%20query%20for%20the%20results)).  
- `BatchInitSessions` (PEP 8: `batch_init_sessions`) – Initialize RTR sessions on multiple hosts (prerequisite for running batch commands) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=BatchGetCmd%20Batch%20executes%20,is%20needed%20on%20the%20host)).  
- `BatchRefreshSessions` (PEP 8: `batch_refresh_sessions`) – Refresh RTR sessions on multiple hosts to keep them alive (sessions expire after 10 minutes without refresh) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=BatchInitSessions%20Batch%20initialize%20a%20RTR,after%2010%20minutes%20unless%20refreshed)).  
- `RTR_CheckActiveResponderCommandStatus` (PEP 8: `check_active_responder_command_status`) – Get the status of an executed active-responder command on a single host ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_CheckActiveResponderCommandStatus%20Get%20status%20of%20an,command%20on%20a%20single%20host)).  
- `RTR_ExecuteActiveResponderCommand` (PEP 8: `execute_active_responder_command`) – Execute an active-responder (elevated) command on a single host session ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_CheckActiveResponderCommandStatus%20Get%20status%20of%20an,command%20on%20a%20single%20host)).  
- `RTR_CheckCommandStatus` (PEP 8: `check_command_status`) – Get the status of an executed (read-only) command on a single host ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_CheckActiveResponderCommandStatus%20Get%20status%20of%20an,command%20on%20a%20single%20host)).  
- `RTR_ExecuteCommand` (PEP 8: `execute_command`) – Execute a standard (read-only) command on a single host session ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_ExecuteActiveResponderCommand%20Execute%20an%20active%20responder,command%20on%20a%20single%20host)).  
- `RTR_GetExtractedFileContents` (PEP 8: `get_extracted_file_contents`) – Download the contents of an extracted file from a host (by session ID and file SHA-256) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_ExecuteCommand%20Execute%20a%20command%20on,for%20the%20specified%20RTR%20session)).  
- `RTR_ListFiles` (PEP 8: `list_files`) – List files available in the current RTR session (files that have been uploaded or retrieved) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_GetExtractedFileContents%20Get%20RTR%20extracted%20file,%28Expanded%20output%20detail)).  
- `RTR_ListFilesV2` (PEP 8: `list_files_v2`) – List files in the session with expanded detail (v2 of list_files) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=session%20and%20sha256,RTR_DeleteFileDelete%20a%20RTR%20session%20file)).  
- `RTR_DeleteFile` (PEP 8: `delete_file`) – Delete a file from the RTR session (remove an uploaded or retrieved file) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_ListFilesV2%20Get%20a%20list%20of,RTR_DeleteFileV2Delete%20a%20RTR%20session%20file)).  
- `RTR_DeleteFileV2` – (PEP 8: `delete_file_v2`) – Delete a session file (v2 endpoint, use with ListFilesV2 for extended info) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_ListFilesV2%20Get%20a%20list%20of,Use%20with%20%20803)).  
- `RTR_ListQueuedSessions` (PEP 8: `list_queued_sessions`) – Get metadata for queued RTR sessions by session ID (for sessions pending execution) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=%28Expanded%20output%20detail,timeout%20on%20a%20single%20host)).  
- `RTR_DeleteQueuedSession` (PEP 8: `delete_queued_session`) – Delete a queued session command (cancel a pending queued RTR action) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=%28Expanded%20output%20detail,timeout%20on%20a%20single%20host)).  
- `RTR_PulseSession` (PEP 8: `pulse_session`) – Refresh/extend the timeout of an active session on a host (keep session alive) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_ListQueuedSessions%20Get%20queued%20session%20metadata,session%20metadata%20by%20session%20id)).  
- `RTR_ListSessions` (PEP 8: `list_sessions`) – Get metadata for an active session by session ID ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_DeleteQueuedSession%20Delete%20a%20queued%20session,session%20with%20the%20RTR%20cloud)).  
- `RTR_InitSession` (PEP 8: `init_session`) – Initialize a new RTR session with a host (obtains a session ID for that host) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_PulseSession%20Refresh%20a%20session%20timeout,811Delete%20a%20session)).  
- `RTR_DeleteSession` (PEP 8: `delete_session`) – Close an RTR session (end session by session ID) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_ListSessions%20Get%20session%20metadata%20by,812Get%20a%20list%20of%20session_ids)).  
- `RTR_ListAllSessions` (PEP 8: `list_all_sessions`) – List all RTR session IDs for the user (all active sessions) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_InitSession%20Initialize%20a%20new%20session,RTR_ListAllSessionsGet%20a%20list%20of%20session_ids)).

**Example – Basic RTR single-host command:** In this example, an RTR session is initiated on a host, a command is executed to list the `C:\` directory, and then the session is closed ([FalconPy_API_Reference.md](file://file-QdkBrgrHc7PMw8LJ8ur2hE#:~:text=from%20falconpy%20import%20RealTimeResponse%20falcon,ls%20C)) ([FalconPy_API_Reference.md](file://file-QdkBrgrHc7PMw8LJ8ur2hE#:~:text=Execute%20a%20command%20%28e,session_id)). 

```python
from falconpy import RealTimeResponse

falcon = RealTimeResponse(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
# Start a session on a device
session = falcon.init_session(body={"device_id": "<AID>"})
session_id = session["resources"][0]["session_id"]

# Execute a command (e.g., list directory contents of C:\)
response = falcon.execute_command(body={
    "base_command": "ls",
    "command_string": "ls C:\\",
    "session_id": session_id
})
print(response)

# Close the session
falcon.delete_session(body={"session_id": session_id})
``` 

*(FalconPy’s RTR methods map to the CrowdStrike RTR API. For multiple hosts, use the batch commands in the RTR Admin service ([FalconPy_API_Reference.md](file://file-QdkBrgrHc7PMw8LJ8ur2hE#:~:text=,Real%20Time%20Response%20Admin%20endpoints)).)*

## Real Time Response Admin

**Description:** **Real Time Response Admin** provides elevated RTR capabilities for incident response, such as running administrative commands (active-responder commands) and managing the script library ([FalconPy_API_Reference.md](file://file-QdkBrgrHc7PMw8LJ8ur2hE#:~:text=Real%20Time%20Response%20Admin)). This service is used for commands that require elevated privileges and for uploading or retrieving scripts and files used in RTR sessions.

**Available Operations:** ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=Operation%20ID%20Description%20BatchAdminCmd%20Batch,metadata%20and%20content%20of%20script)) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_GetPut_Files%20Get%20put,command)) The `RealTimeResponseAdmin` class includes operations for executing admin-level commands in RTR and handling scripts/files:  

- `BatchAdminCmd` (PEP 8: `batch_admin_command`) – Batch execute an *administrator* command on multiple hosts via a batch ID ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=Operation%20ID%20Description%20BatchAdminCmd%20Batch,of%20an%20executed%20RTR%20administrator)).  
- `RTR_CheckAdminCommandStatus` (PEP 8: `check_admin_command_status`) – Get the status of an executed admin command on a single host ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=BatchAdminCmd%20Batch%20executes%20a%20RTR,administrator%20command%20on%20a%20single)).  
- `RTR_ExecuteAdminCommand` (PEP 8: `execute_admin_command`) – Execute an admin command on a single host (within an active session) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=mapped%20to%20the%20given%20batch,command%20on%20a%20single%20host)).  
- `RTR_GetFalconScripts` (PEP 8: `get_falcon_scripts`) – Retrieve CrowdStrike-provided **Falcon Scripts** (built-in RTR scripts) with metadata and content ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=command%20on%20a%20single%20host,metadata%20and%20content%20of%20script)).  
- `RTR_GetPut_Files` (PEP 8: `get_put_files`) – Retrieve **put-files** (files available for the RTR `put` command) by their IDs ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=host,metadata%20and%20content%20of%20script)).  
- `RTR_GetPut_FilesV2` (PEP 8: `get_put_files_v2`) – Retrieve put-files by ID (v2 version with potentially different output format) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_GetPut_Files%20Get%20put,command)).  
- `RTR_CreatePut_Files` (PEP 8: `upload_put_file`) – Upload a new file to the put-files library (to be used with the RTR `put` command) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_GetPut_Files%20Get%20put,command)).  
- `RTR_DeletePut_Files` (PEP 8: `delete_put_file`) – Delete a put-file from the library by ID (one file at a time) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_CreatePut_FilesUpload%20a%20new%20put,command)).  
- `RTR_GetScripts` (PEP 8: `get_scripts`) – Retrieve custom RTR **scripts** by their IDs (for use with the `runscript` command) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_DeletePut_Files%20Delete%20a%20put,Can%20only)).  
- `RTR_GetScriptsV2` (PEP 8: `get_scripts_v2`) – Retrieve custom scripts by ID (v2 endpoint) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_DeletePut_Files%20Delete%20a%20put,Can%20only)).  
- `RTR_CreateScripts` (PEP 8: `upload_script`) – Upload a new **custom script** to the RTR scripts library (for `runscript`) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_GetScriptsV2%20Get%20custom,IDs%20available%20to%20the%20user)).  
- `RTR_DeleteScripts` (PEP 8: `delete_script`) – Delete a custom script by ID (removes it from the library) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_CreateScripts%20Upload%20a%20new%20custom,that%20are%20available%20to%20the)).  
- `RTR_UpdateScripts` (PEP 8: `update_script`) – Replace an existing custom script with new content (upload new version) ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=for%20the%20RTR%20,that%20are%20available%20to%20the)).  
- `RTR_ListFalconScripts` (PEP 8: `list_falcon_scripts`) – List all available Falcon (built-in) script IDs that the user can run ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_UpdateScripts%20Upload%20a%20new%20scripts,command)).  
- `RTR_ListPut_Files` (PEP 8: `list_put_files`) – List all available put-file IDs that can be used with `put` on RTR ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_UpdateScripts%20Upload%20a%20new%20scripts,command)).  
- `RTR_ListScripts` (PEP 8: `list_scripts`) – List all available custom script IDs in the library ([Operations by Collection](https://www.falconpy.io/Operations/Operations-by-Collection.html#:~:text=RTR_ListFalconScripts%20Get%20a%20list%20of,command)).

**Example – List custom RTR scripts:** The following example uses the RTR Admin service to retrieve a list of custom scripts available to run via RTR. This could be useful during IR to see what response scripts are already uploaded.

```python
from falconpy import RealTimeResponseAdmin

falcon = RealTimeResponseAdmin(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
# Retrieve IDs of all custom scripts in the RTR scripts library
response = falcon.list_scripts()
print(response)
```

*(In practice, using admin commands often involves first initializing an RTR session (using `RealTimeResponse.init_session`) and then calling `execute_admin_command` with the session ID. The batch admin commands require a batch ID obtained via `batch_init_sessions` in RTR ([FalconPy_API_Reference.md](file://file-QdkBrgrHc7PMw8LJ8ur2hE#:~:text=,Real%20Time%20Response%20Admin%20endpoints)).)*

## Real Time Response Audit

**Description:** **Real Time Response Audit** allows retrieval of RTR session audit logs and history ([FalconPy_API_Reference.md](file://file-QdkBrgrHc7PMw8LJ8ur2hE#:~:text=Real%20Time%20Response%20Audit)). This service provides visibility into all RTR sessions and commands executed, which is useful for incident review and compliance.

**Available Operations:** The `RealTimeResponseAudit` class focuses on retrieving session data:  

- `RTRAuditSessions` (PEP 8: `audit_sessions`) – Get all RTR sessions (with associated command info if requested) that were created for the customer within a specified time period ([Real Time Response Audit](https://www.falconpy.io/Service-Collections/Real-Time-Response-Audit.html#:~:text=Operation%20ID%20Description%20RTRAuditSessions%20PEP8,customer%20in%20a%20specified%20duration)) ([Real Time Response Audit](https://www.falconpy.io/Service-Collections/Real-Time-Response-Audit.html#:~:text=RTRAuditSessions)). *(This endpoint supports filtering by time or other criteria, and an option to include command details in the results.*)

*(The RTR Audit API may also include more granular endpoints to query specific command or session details, but FalconPy consolidates audit retrieval into the `audit_sessions` method ([Real Time Response Audit](https://www.falconpy.io/Service-Collections/Real-Time-Response-Audit.html#:~:text=Operation%20ID%20Description%20RTRAuditSessions%20PEP8,customer%20in%20a%20specified%20duration)).)*

**Example – Retrieve RTR audit log:** This example fetches a list of RTR sessions (audit log). A filter can be applied (e.g., by date range or host). By default, command details are excluded unless `with_command_info=True` is used ([Real Time Response Audit](https://www.falconpy.io/Service-Collections/Real-Time-Response-Audit.html#:~:text=RTRAuditSessions%20PEP8%20audit_sessions%20Get%20all,customer%20in%20a%20specified%20duration)) ([Real Time Response Audit](https://www.falconpy.io/Service-Collections/Real-Time-Response-Audit.html#:~:text=parametersImage%3A%20Service%20Class%20SupportImage%3A%20Uber,fields)).

```python
from falconpy import RealTimeResponseAudit

falcon = RealTimeResponseAudit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
# Retrieve recent RTR sessions (audit log). For example, limit to 50 sessions:
audit_log = falcon.audit_sessions(limit=50, sort="started_at|desc")
print(audit_log)
```

---

## Recon

**Description:** Interact with **Falcon Recon** (which might refer to the Falcon X Recon/Dark Web monitoring service).

**Available Operations:** 

- `QueryNotifications` – Query Recon notification IDs.  
- `GetNotifications` – Get Recon notification details.  
- `AcknowledgeNotifications` – Acknowledge (mark as read) Recon notifications.  
- `GetRuleDetails` – Get details of Recon rules.  
- `UpdateRules` – Enable/disable or update Recon rules.  

**Example – Acknowledge a Recon notification:**

```python
from falconpy import Recon
falcon = Recon(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
notifs = falcon.query_notifications(limit=1)
notif_id = notifs["resources"][0] if notifs["resources"] else None
if notif_id:
    falcon.acknowledge_notifications(body={"ids": [notif_id]})
```

---

## Report Executions

**Description:** Manage **Report Executions** (likely scheduled reports generation and statuses).

**Available Operations:** 

- `QueryReportExecutions` – Query report execution IDs.  
- `GetReportExecutions` – Get details/status of report executions.  
- `CancelReportExecution` – Cancel a running report execution.  

**Example:**

```python
from falconpy import ReportExecutions
falcon = ReportExecutions(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
executions = falcon.query_report_executions(filter="status:'Executing'")
print(executions)
```

---

## Response Policies

**Description:** Manage **Real Time Response Policies** (which hosts are allowed for RTR and with what level).

**Available Operations:** 

- `QueryResponsePolicies` – Query RTR policy IDs.  
- `GetResponsePolicies` – Get RTR policy details.  
- `CreateResponsePolicies` – Create new RTR policies.  
- `UpdateResponsePolicies` – Update RTR policies.  
- `DeleteResponsePolicies` – Delete RTR policies.  
- `QueryResponsePolicyMembers` – Query members of an RTR policy.  

**Example – CreateResponsePolicies:**

```python
from falconpy import ResponsePolicies
falcon = ResponsePolicies(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
new_policy = {
    "name": "Limited RTR Policy",
    "settings": { "allow_commands": False }  # hypothetical setting
}
response = falcon.create_response_policies(body={"resources": [new_policy]})
print(response)
```

---

## Sample Uploads

**Description:** **Sample Uploads** – upload malware samples to CrowdStrike for analysis (Falcon X sandbox or analysis queue).

**Available Operations:** 

- `UploadSampleV2` (PEP 8: `upload_sample`) – Upload a file sample for malware analysis.  
- `GetSampleV2` (PEP 8: `get_sample`) – Retrieve a sample by ID (or its metadata).  
- `DeleteSampleV2` – Delete a sample from the repository.  
- `QuerySamples` – Query sample IDs by filter.  

**Example – UploadSampleV2:**

```python
from falconpy import SampleUploads
falcon = SampleUploads(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
file_path = "/path/to/malware.exe"
with open(file_path, "rb") as f:
    file_content = f.read()
response = falcon.upload_sample(file_name="malware.exe", file_data=file_content, is_confidential=True)
print(response)
```

*(The SDK might allow direct file path usage; check official docs. The above demonstrates reading and passing bytes.)*

---

## Scheduled Reports

**Description:** Manage **Scheduled Reports** settings.

**Available Operations:** 

- `GetScheduledReports` – Get scheduled report definitions.  
- `CreateScheduledReports` – Create a new scheduled report.  
- `UpdateScheduledReports` – Update scheduled report.  
- `DeleteScheduledReports` – Delete scheduled report.  
- `QueryScheduledReports` – Query scheduled report IDs.  

**Example – CreateScheduledReports:**

```python
from falconpy import ScheduledReports
falcon = ScheduledReports(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
new_report = {
    "name": "Weekly Detections Report",
    "cron_schedule": "0 0 * * 0",  # weekly on Sunday midnight
    "report_type": "detections_summary"
}
response = falcon.create_scheduled_reports(body={"resources": [new_report]})
print(response)
```

---

## Sensor Download

**Description:** **Sensor Download** service – get download URLs or information for sensor installers.

**Available Operations:** 

- `GetSensorInstallersEntities` – Get details (including download URLs) for specified sensor installers by ID.  
- `GetSensorInstallersCCIDByQuery` – Get download link for a sensor installer by specifying the OS and other parameters.  
- `GetCombinedSensorInstallers` – Combined query of sensor installers.  
- `GenerateSensorDownloadLink` (PEP 8: `generate_sensor_download_link`) – Generate a download URL for a given sensor installer.

**Example – GenerateSensorDownloadLink:**

```python
from falconpy import SensorDownload
falcon = SensorDownload(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
# Suppose we know an installer ID from a previous query:
installer_id = "abcdef1234567890"
link_info = falcon.generate_sensor_download_link(body={"id": installer_id})
print(link_info)  # Contains a pre-signed URL for downloading the installer
```

---

## Sensor Update Policy

**Description:** Manage **Sensor Update Policies** (policies controlling sensor update versions).

**Available Operations:** 

- `QuerySensorUpdatePolicies` – Query sensor update policy IDs.  
- `GetSensorUpdatePolicies` – Get details of sensor update policies by ID.  
- `CreateSensorUpdatePolicies` – Create new update policies.  
- `UpdateSensorUpdatePolicies` – Update existing update policies.  
- `DeleteSensorUpdatePolicies` – Delete update policies.  
- `UpdateSensorUpdatePolicyPrecedence` – Change policy precedence.  
- `QuerySensorUpdatePolicyMembers` – Query members (hosts) of a sensor update policy.

**Example – UpdateSensorUpdatePolicies (e.g., change version):**

```python
from falconpy import SensorUpdatePolicy
falcon = SensorUpdatePolicy(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
policy_id = "<policy-id>"
update_payload = {
  "id": policy_id,
  "settings": { "version": "6.31.0" }  # set sensors to version 6.31
}
response = falcon.update_sensor_update_policies(body={"resources": [update_payload]})
print(response)
```

---

## Sensor Usage

**Description:** Retrieve **Sensor Usage** metrics (information about sensor counts, etc).

**Available Operations:** 

- `GetSensorUsage` – Get sensor usage over time (perhaps weekly fetch counts).  
- `GetSensorUsageSummary` – Get a summary of sensor usage.  
- `QuerySensorUsage` – Query usage data.

**Example – GetSensorUsageWeekly:**

```python
from falconpy import SensorUsage
falcon = SensorUsage(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
usage = falcon.get_sensor_usage()  # might require parameters for timeframe
print(usage)
```

*(If the API requires specific date ranges, pass them as query params like `start_date`/`end_date`.)*

---

## Sensor Visibility Exclusions

**Description:** Manage **Sensor Visibility Exclusions** (exclusions that prevent the sensor from uploading certain data or observing certain paths).

**Available Operations:** 

- `QuerySensorVisibilityExclusions` – Query sensor visibility exclusion IDs.  
- `GetSensorVisibilityExclusions` – Get details of sensor visibility exclusions by ID.  
- `CreateSensorVisibilityExclusions` – Create new exclusions.  
- `UpdateSensorVisibilityExclusions` – Update exclusions.  
- `DeleteSensorVisibilityExclusions` – Delete exclusions.  

**Example – CreateSensorVisibilityExclusions:**

```python
from falconpy import SensorVisibilityExclusions
falcon = SensorVisibilityExclusions(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
new_exclusion = {
    "value": "C:\\SecretFolder\\*",
    "platform_name": "Windows",
    "description": "Exclude secret folder from sensor visibility"
}
response = falcon.create_sensor_visibility_exclusions(body={"resources": [new_exclusion]})
print(response)
```

---

## Spotlight Evaluation Logic

**Description:** Retrieve **Spotlight Evaluation Logic** details (how certain compliance or vulnerability rules are evaluated).

**Available Operations:** 

- `GetSpotlightEvaluationLogic` – Get the evaluation logic for Spotlight (e.g., how a certain check is done).  
- `QuerySpotlightEvaluationLogic` – Query logic IDs.

**Example:**

```python
from falconpy import SpotlightEvaluationLogic
falcon = SpotlightEvaluationLogic(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
logic = falcon.get_spotlight_evaluation_logic(ids=["logic_id_1"])
print(logic)
```

---

## Spotlight Vulnerabilities

**Description:** Access **Spotlight Vulnerabilities** data (endpoint vulnerabilities detected by Falcon Spotlight).

**Available Operations:** 

- `QueryVulnerabilities` – Query vulnerability IDs by filter (e.g., by host, severity).  
- `GetVulnerabilities` – Get vulnerability details (including CVE, host affected, status).  
- `QueryVulnerabilityIdsByDevice` – Given a host ID, get vulnerability IDs on that host.  
- `UpdateVulnerabilityStatuses` – Update status (e.g., ignored, mitigated) of vulnerabilities.

**Example – QueryVulnerabilities:**

```python
from falconpy import SpotlightVulnerabilities
falcon = SpotlightVulnerabilities(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
resp = falcon.query_vulnerabilities(filter="cve_id:'CVE-2021-34527'")
vuln_ids = resp.get("resources", [])
if vuln_ids:
    details = falcon.get_vulnerabilities(ids=vuln_ids[:5])
    print(details)
```

---

## Tailored Intelligence

**Description:** Access **Tailored Intelligence** (custom intelligence indicators or reports tailored to the customer).

**Available Operations:** 

- *(Operations likely to query tailored threat reports, indicators, etc. Provide representative example if possible.)*

---

## ThreatGraph

**Description:** Interact with **ThreatGraph** API (graph of threat events and relationships).

**Available Operations:** 

- `QueryThreatGraph` – Query ThreatGraph for relationships between entities (like an indicator and devices).  
- `GetThreatGraphEntities` – Retrieve details on ThreatGraph nodes (devices, users, etc.).  

*(The ThreatGraph API can be complex. Provide usage as per official docs.)*

---

## Unidentified Containers

**Description:** Manage **Unidentified Containers** – likely container instances that are not identified or inventoried.

**Available Operations:** 

- `QueryUnidentifiedContainers` – Query IDs of unidentified containers.  
- `GetUnidentifiedContainers` – Get details of unidentified containers by ID.  

**Example:**

```python
from falconpy import UnidentifiedContainers
falcon = UnidentifiedContainers(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
ids = falcon.query_unidentified_containers(limit=10)["resources"]
details = falcon.get_unidentified_containers(ids=ids)
print(details)
```

---

## User Management

**Description:** Manage **Users and Roles** in the Falcon platform.

**Available Operations:**

- `QueryUsers` – Query user IDs by filter.  
- `GetUserDetails` (PEP 8: `get_user_details`) – Get details for specific user IDs.  
- `CreateUser` – Create a new user in the customer account.  
- `UpdateUser` – Update an existing user's information.  
- `DeleteUser` – Delete a user.  
- `QueryRoles` – Query role IDs.  
- `GetRoles` – Get role details.  
- `GrantUserRole` / `RevokeUserRole` – Manage user role assignments.  

**Example – CreateUser:**

```python
from falconpy import UserManagement
falcon = UserManagement(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
new_user = {
    "first_name": "John",
    "last_name": "Doe",
    "password": "SecurePassword123!",
    "username": "jdoe@example.com",
    "roles": ["roleid1", "roleid2"]
}
response = falcon.create_user(body=new_user)
print(response)
```

---

## Workflows

**Description:** Manage **Workflows** in Falcon (case management and automation workflows).

**Available Operations:** 

- `QueryWorkflows` – Query workflow IDs.  
- `GetWorkflows` – Get workflow details by ID.  
- `CreateWorkflow` – Create a new workflow.  
- `UpdateWorkflow` – Update a workflow.  
- `DeleteWorkflow` – Delete a workflow.  
- `ExecuteWorkflow` – Trigger a workflow execution on an entity (like an incident).  

**Example – ExecuteWorkflow:**

```python
from falconpy import Workflows
falcon = Workflows(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
response = falcon.execute_workflow(body={
    "workflow_id": "<workflow-id>",
    "entity_id": "<incident-or-entity-id>"
})
print(response)
```

---

## Zero Trust Assessment

**Description:** Retrieve **Zero Trust Assessment (ZTA)** scores and audits for hosts. ZTA provides a score for each host indicating its Zero Trust posture.

**Available Operations:**

- `getAssessmentV1` (PEP 8: `get_assessment`) – Get Zero Trust Assessment data for one or more hosts by providing agent IDs and a customer ID.  
- `getAuditV1` (PEP 8: `get_audit`) – Get the Zero Trust Assessment audit report for one customer ID. *(Operation ID recently changed; see note below.)*  
- `getAssessmentsByScoreV1` (PEP 8: `get_assessments_by_score`) – Get Zero Trust Assessment data for hosts within a range of scores.

### getAssessmentV1

Get Zero Trust Assessment data for one or more hosts by providing agent IDs (AIDs) and your customer ID (CID).

**PEP 8 method name:** `get_assessment`

**Endpoint:** `GET /zero-trust-assessment/entities/assessments/v1`  

**Required Scope:** `zero-trust-assessment:read`  

**Parameters (Query):**  
- **ids** (string or list of strings): One or more agent IDs for which to retrieve ZTA scores. *(Multiple IDs can be comma-separated in a single string or provided as a list.)*  
- **parameters** (`dict`, optional): Full query parameters as JSON (not needed if using `ids` and other keyword args directly).

**Example Usage:**

- *Service class (PEP8 syntax)*:  
  ```python
  from falconpy import ZeroTrustAssessment
  falcon = ZeroTrustAssessment(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
  id_list = "hostAID1,hostAID2"  # could also be ["hostAID1","hostAID2"]
  response = falcon.get_assessment(ids=id_list)
  print(response)
  ```  

- *Service class (Operation ID syntax)*:  
  ```python
  response = falcon.getAssessmentV1(ids=id_list)
  print(response)
  ```  

- *Uber class example*:  
  ```python
  from falconpy import APIHarnessV2
  falcon = APIHarnessV2(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
  response = falcon.command("getAssessmentV1", ids=id_list)
  print(response)
  ```  

### getAuditV1

Get the Zero Trust Assessment **audit report** for your customer (one CID). 

> **Note:** This operation ID was recently changed from a legacy name. FalconPy supports the old ID `getComplianceV1` (method `get_compliance`) via alias, but use `getAuditV1` going forward.

**PEP 8 method name:** `get_audit`  
**Legacy Operation ID:** `getComplianceV1` (PEP8: `get_compliance`) – supported as alias.

**Endpoint:** `GET /zero-trust-assessment/entities/audit/v1`  

**Required Scope:** `zero-trust-assessment:read`  

**Parameters:** *None.* (The API uses the authenticated user’s CID to fetch the audit report; no additional query parameters needed.)

**Example Usage:**

- *Service class (PEP8 syntax)*:  
  ```python
  response = falcon.get_audit()
  print(response)
  ```  

- *Service class (Operation ID syntax)*:  
  ```python
  response = falcon.getAuditV1()
  print(response)
  ```  

- *Uber class example*:  
  ```python
  response = falcon.command("getAuditV1")
  print(response)
  ```  

### getAssessmentsByScoreV1

Get Zero Trust Assessment data for one or more hosts by providing a score range (and CID). This allows fetching all hosts whose ZTA score falls within a specified range.

**PEP 8 method name:** `get_assessments_by_score`

**Endpoint:** `GET /zero-trust-assessment/queries/assessments/v1`  

**Required Scope:** `zero-trust-assessment:read`  

**Parameters (Query):**  
- **filter** (string): FQL filter string to filter hosts (e.g., by some criteria aside from score – optional).  
- **limit** (integer): Number of records to return (min 1, max 1000, default 100).  
- **after** (string): Pagination token used with `limit` for paging results. Omit on first request; use the `after` token from the previous response for subsequent pages.  
- **sort** (string): FQL sort string. Only one sort field is allowed (`score`). E.g., `"score|asc"` or `"score|desc"`.  
- **parameters** (`dict`, optional): Full query params in JSON form (not required if using other params directly).

**Example Usage:**

- *Service class (PEP8 syntax)*:  
  ```python
  response = falcon.get_assessments_by_score(
      filter="string",      # e.g., filter by some other field if needed
      limit=100,
      after="string_token", # pagination token if continuing
      sort="score|desc"
  )
  print(response)
  ```  

- *Service class (Operation ID syntax)*:  
  ```python
  response = falcon.getAssessmentsByScoreV1(
      filter="string",
      limit=100,
      after="string_token",
      sort="score|desc"
  )
  print(response)
  ```  

- *Uber class example*:  
  ```python
  response = falcon.command("getAssessmentsByScoreV1",
                             filter="string",
                             limit=100,
                             after="string_token",
                             sort="score|desc")
  print(response)
  ```  



This concludes the FalconPy Service Collections reference. Each section above should provide software engineers the necessary information to integrate directly with the FalconPy SDK for the respective API service: including all operation names, accepted parameters, and example usage patterns. By following these examples and using the PEP 8 method names provided, developers can confidently call any CrowdStrike Falcon API endpoint through FalconPy.
