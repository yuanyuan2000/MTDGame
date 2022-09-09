# event

## MTD event:

 - Trigger MTD: mtd_trigger_action
 - Execute MTD: execute_or_suspend -> mtd_execute_action
 - Suspend MTD: execute_or_suspend -> suspended

## Attack event:

 - Trigger Attack: host_scan_and_setup_host_enum
 - Port scan: start_and_process_port_scan
 - Exploit vulnerabilities: find_and_exploit_vulns
 - Brute force: brute_force_users_login
