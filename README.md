This module is to be used with the webhook Grafana alerting channel. It launches a web-server that listens for POST data with alert details (posted by Grafana every time an event occurs with any of the defined alerts in the GUI). The module captures the POST output (it comes in JSON format), processes it and stores it in a MySQL DB as a unique event.

Second step is a MySQL datasource created in Grafana that uses this DB to retreive the events and display them back in GUI ordered by timestamp, similarly as Zabbix does with the Problems page.

Main parts of this setup are the grafana_alerts.py main script that also acts as the web-server that listens for the alert data, a requirements file with the needed python modules, a MySQL DB for which we have the SQL to create the table, and a db.conf file with DB connection details.

SQL code for the table that will store the events:

```sql
CREATE TABLE `alerts` (
  `id` int(8) NOT NULL AUTO_INCREMENT,
  `time` datetime DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  `value` decimal(65,4) DEFAULT NULL,
  `metric` text,
  `state` varchar(190) DEFAULT NULL,
  `alertLink` text,
  `dashboardName` varchar(200) DEFAULT NULL,
  `message` text,
  `ruleId` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

`The DB instance name will be grafana_alerts. Also, a grafana_user will need to be created with permissions to SELECT, INSERT and UPDATE.`

The DB details are stored in a separate file:

{"host": "localhost", "user": "grafana_alerts", "password": "grafana_pass", "db": "grafana_alerts"}

New in version 0.3 there is now logging functionality added. Be default, the log_level is INFO. It can be overwritten by defining in the compose file an environment variable named LOG_LEVEL. It accepts the standard log levels: CRITICAL" "ERROR" "WARNING" "INFO" "DEBUG" and "NOTSET".
