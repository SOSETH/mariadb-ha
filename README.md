# MariaDB

Tested on: Debian 9

Configure a mariadb galera cluster for SOSETH use (mainly monitoring).

## Dependencies
* [SOSETH/haproxy](https://github.com/SOSETH/haproxy)
* Certificates in `/etc/haproxy`. Check `templates/haproxy-dropin.j2` for details or use the following config for [SOSETH/local-ca](https://github.com/SOSETH/local-ca):
```
- role: local-ca
  caname: galera
  client:
    cert: /etc/haproxy/mdb-cl.crt
    key: /etc/haproxy/mdb-cl.key
    cn: "{{ ansible_nodename }}-client"
  ca:
    cert: /etc/haproxy/mdb-ca.crt
    crl: "/etc/haproxy/mdb-crl.pem"
  server:
    cert: /etc/haproxy/mdb-sv.crt
    key: /etc/haproxy/mdb-sv.key
    cn: "{{ ansible_nodename }}-server"
```
* iptables for blocking external IST/SST port access

## Configuration
|Var|Default value|Description|
|---|-------------|-----------|
|mariadb_ha_group|mon_server|The host group to deploy the cluster on|
|mariadb_ha_root_password|`mariadb_root_password`|The password to set for root. Must be the same one as the [mariadb role](https://github.com/SOSETH/mariadb) and therefore defaults to the same value|
|mariadb_ha_dump_password|None|Passwort for the database dump user (required for SST). You need to set this|
|mariadb_ha_databases|`[]`| List of dicts of databases/users to create. Each entry has a name, user and passwort attribute, specifying a database and a user to access this database. The user will be granted all privileges on the database. |
|mariadb_listen_port|3307|Default listen ports. This needs to be _unique_ on the system because MariaDB will complain even if you bind the same port to different interfaces. |
|mariadb_ha_ports|(see `defaults/main.yml`)|Port mapping for HAProxy|
|mariadb_public_port_offset|1000|Offset public ports by this amount|
|mariadb_ha_cluster_name|ansiblecluster|Name of the cluster|

## Overview
This role will set up a MariaDB Galera cluster, tunneling all inter-node
communication through HAProxy so that it gets encrypted and authenticated.
During normal operation, you'll notice that a Galera Cluster is not reboot-safe
(as in, it does not survive a shutdown and subsequent powerup of all nodes).
Initially, and after every full shutdown, you'll need to pick a node and manually
do
```
galera_new_cluster mariadb@galera.service
```
to bootstrap the service. Afterwards, the service can be restarted on the other
nodes but take into account that any given node can only transfert state to
a single other node during SST at a time.
On initial setup, it does not matter which node you execute this command on.
On subsequent cluster bootstraps, you'll need to pick the node with the highest
`seqno` in `/var/lib/mysql-ha/grastate.dat`. Picking the wrong node *will* lead
to data loss, you have been warned!

## Technical details
MariaDB Galera operates over multiple ports: The ordinary cluster state protocol
happens on port 4567 and is fairly easy to tunnel. The more involved part turns
out to be the initial state snapshot transfer (SST). Normally, mariadb will invoke
a script starting rsync (without SSH AFAIU), which is cumbersome to tunnel. Instead,
this role uses mariadbdump, which pipes the resulting dumps via socat. Since
socat would normally bind to all interfaces (and therefore clash with HAProxy),
we ship a modified SST script (`/usr/bin/wsrep_sst_mariabackup_cst`) that takes
care of binding correctly.
Additionally, all ports except the normal database listen port bind to all
interfaces and would therefore be available publicly, which is why we also use
a systemd dropin to restrict access to those ports to localhost only (HAProxy)
using iptables.

## License
GPLv3, except `templates/wsrep_sst_mariabackup.j2`, which is GPLv2 and
```
Copyright (C) 2013 Percona Inc
Copyright (C) 2017 MariaDB
```
