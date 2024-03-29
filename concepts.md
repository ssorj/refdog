# Skupper concepts

#### Contents

* [Skupper sites and links](#skupper-sites-and-links)
  * [Network](#network)
  * [Site](#site)
  * [Link](#link)
  * [Token](#token)
* [Skupper listeners and connectors](#skupper-listeners-and-connectors)
  * [Listener](#listener)
  * [Connector](#connector)
  * [Routing key](#routing-key)
* [Skupper applications and components](#skupper-applications-and-components)
  * [Application](#application)
  * [Component](#component)
  * [Process](#process)

## Skupper sites and links

A Skupper **network** is composed of **sites**.  A site is a place
where components of your distributed application are running.

Sites use **links** to form a dedicated network for your application.
These links are the basis for site-to-site and service-to-service
communication.  Links are always secured using mutual TLS
authentication and encryption.

In this example, "site-1" and "site-2" are linked to form the network
for the "Hello World" application.

~~~
+------------------------------------------------+
|              Network "Hello World"             |
|                                                |
| +---------------+            +---------------+ |
| | Site "site-1" |--- Link ---| Site "site-2" | |
| +---------------+            +---------------+ |
+------------------------------------------------+
~~~

To create a link, the site that is to be the target of the link must
have a point of ingress, so it can accept a TCP connection.

In this example, site "site-1" accepts incoming TCP connections through
its ingress, and site "site-2" creates the site-to-site link by
establishing an outbound TCP connection to "site-1".

~~~
+----------------------------------------------+
|             Network "Hello World"            |
|                                              |
| +-----------------+       +----------------+ |
| |  Site "site-1"  |       |  Site "site-2" | |
| |                 |       |                | |
| |   +---------+   |       |   +--------+   | |
| |   | Ingress |<--------------|  Link  |   | |
| |   +---------+   |       |   +--------+   | |
| +-----------------+       +----------------+ |
+----------------------------------------------+
~~~

Creating a link requires explicit permission from the target site.
This permission is granted using **tokens**.  A token contains a URL
for the target site and a secret key.

In this example, site "site-1" wishes to allow "site-2" to create a link.
Site "site-1" creates a token.  The owner of "site-1" gives the token to
the owner of "site-2".  The owner of "site-2" then uses the token to
create the link.

~~~
 +---------------+           +---------------+
 | Site "site-1" |           | Site "site-2" |
 +---------------+           +---------------+
         |                           |
+-----------------+                  |
| 1. Create token |                  |
+-----------------+                  |
         |                           |
         |   +-------------------+   |
         |---| 2. Transfer token |-->|
         |   +-------------------+   |
         |                           |
         |    +----------------+     |
         |<---| 3. Create link |-----|
         |    +----------------+     |
         |                           |
~~~

Skupper networks are small: they are scoped to the application they
support.  A single platform instance such as a Kubernetes cluster can
host many Skupper networks.

~~~
+-------------------------------+      +------------------------------+
|      Kubernetes cluster 1     |      |      Kubernetes cluster 2    |
|                               |      |                              |
|   +-------------------------------------------------------------+   |
|   |                           Network 1                         |   |
|   +-------------------------------------------------------------+   |
|                               |      |                              |
|   +-------------------------------------------------------------+   |
|   |                           Network 2                         |   |
|   +-------------------------------------------------------------+   |
|                               |      |                              |
|   +-------------------------------------------------------------+   |
|   |                           Network N                         |   |
|   +-------------------------------------------------------------+   |
|                               |      |                              |
+-------------------------------+      +------------------------------+
~~~

Skupper works on multiple platforms: Kubernetes, Podman, virtual
machines, and bare metal hosts.  Each site in a network can run on any
supported platform.

~~~
+-----------------------------+      +------------------------+      +-------------------------+
|      Kubernetes cluster     |      |         Podman         |      |     VM or bare metal    |
|                             |      |                        |      |                         |
|  +-----------------------+  |      |  +------------------+  |      |  +-------------------+  |
|  |     Site "site-1"     |  |      |  |  Site "central"  |  |      |  |   Site "site-2"   |  |
|  |                       |  |      |  |                  |  |      |  |                   |  |
|  |   Namespace "site-1"  |--- Link ---|  Podman network  |--- Link ---|    Local user     |  |
|  |                       |  |      |  |    "skupper"     |  |      |  |                   |  |
|  +-----------------------+  |      |  +------------------+  |      |  +-------------------+  |
+-----------------------------+      +------------------------+      +-------------------------+
~~~

A site does not need to be directly linked to all the other sites in a
network.  A site only needs to be *reachable* through the site
network.  Skupper is responsible for routing connections and requests
to the sites providing the required services.

~~~
 +-----------+                                   +-----------+
 | Site "nw" |---.                           .---| Site "ne" |
 +-----------+    \   +-----------------+   /    +-----------+
       |           :--| Site "central1" |--:           |
+-------------+   /   +-----------------+   \   +-------------+
| Site "west" |--:             |             :--| Site "east" |
+-------------+   \   +-----------------+   /   +-------------+
       |           :--| Site "central2" |--:           |
 +-----------+    /   +-----------------+   \    +-----------+
 | Site "sw" |---'                           '---| Site "se" |
 +-----------+                                   +-----------+
~~~

### Network

A network (also called an "application network" or "service network")
is a set of linked sites.  Each site in the network can expose
services to other sites in the network.  In turn, each site in the
network can access those exposed services.

A network is scoped to one distributed application and is fully
isolated from any other Skupper network.

### Site

A site is a location where components of your application are running.
Sites are linked together to form a network.

Sites have different kinds based on platform.  These include
Kubernetes, Podman, virtual machines, and bare metal hosts.

### Link

A link is a site-to-site communication channel.  Links serve as a
transport for application traffic such as connections and requests.
Links are always encrypted using mutual TLS.

### Token

A token is required to create a link.  The token contains a URL, which
locates the ingress of the target site, and a secret, which represents
the authority to create a link.

Tokens can be restricted to a chosen number of uses inside a limited
time window.  By default, tokens allow only one use and expire after
15 minutes.

## Skupper listeners and connectors

Site-to-site links are distinct from service-to-service connections.
Site links form the underlying transport for your network.  Service
connections are carried on top of this transport.  Service connections
can be established in either direction, regardless of how the site
link was established.

In this example, sites "site-1" and "site-2" have links to site "central".
Workload "frontend" is running on "site-1", and workload "backend" on
"site-2".  When "frontend" connects to "backend", it can ignore the
underlying link topology.  Skupper ensures that "frontend" can connect
directly to "backend".

~~~
Service connection    +---------------------+                              +--------------------+
layer                 | Workload "frontend" |-------- Connection --------->| Workload "backend" |
                      +---------------------+                              +--------------------+
                                |                                                    |
-------------------------------------------------------------------------------------------------
                                |                                                    |
Site link layer        +---------------+          +----------------+          +---------------+
                       | Site "site-1" |-- Link ->| Site "central" |<- Link --| Site "site-2" |
                       +---------------+          +----------------+          +---------------+
~~~

**Listeners** and **connectors** work together to route service
connections across the network.  Listeners provide a local connection
endpoint for remote services.  Connectors specify the local processes
that handle remote service connections.

Listeners and connectors are linked by matching **routing keys**.
Connections to a listener with a given routing key are forwarded to
remote connectors with the same routing key.

In site "site-1", workload "frontend" needs to connect to
`backend:8080`.  Skupper provides a local connection listener for that
host and port.

In "site-2", "backend" is running and ready to handle requests.  Skupper
provides a local connector associated with the processes implementing
"backend".

When "frontend" in "site-1" connects to the listener, Skupper uses the
routing key to forward the connection data to the matching connector
in "site-2", which then connects to the "backend" workload.

~~~
+-------------------------------+                        +--------------------------------+
|         Site "site-1"         |                        |          Site "site-2"         |
|                               |                        |                                |
|    +---------------------+    |                        |     +--------------------+     |
|    | Workload "frontend" |    |                        |     | Workload "backend" |     |
|    +---------------------+    |                        |     +--------------------+     |
|               |               |                        |                ^               |
|           Connection          |                        |                |               |
|               |               |                        |            Connection          |
|               v               |   +----------------+   |                |               |
|   +-----------------------+   |   |  Routing key   |   |   +------------------------+   |
|   | Listener backend:8080 |-------| "backend:8080" |-------| Connector backend:8080 |   |
|   +-----------------------+   |   +----------------+   |   +------------------------+   |
+-------------------------------+                        +--------------------------------+
~~~

<!-- XXX Multiple providers at different sites (load balancing, HA) -->
<!-- ~~~ -->
<!-- XXX -->
<!-- ~~~ -->

### Listener

A listener is a local connection endpoint that is associated with
remote servers.  Listeners expose a host and port for accepting
connections.  Listeners use a routing key to forward connection data
to remote connectors.

### Connector

A connector binds local servers (pods, containers, or processes) to
connection listeners in remote sites.  Connectors are linked to
listeners by a matching routing key.

### Routing key

A routing key is a string identifier that binds connectors and
listeners.  Routing keys are the basis for routing service traffic
across sites.

<!-- ### Services -->

<!-- service - a logical representation of a service\ -->
<!-- server - an actual pod implementing a given service\ -->
<!-- client - something that uses a service -->

<!-- The ultimate purpose of Skupper is to enable application components (microservices) to communicate across distinct sites. -->
<!-- Providing services and requiring services. -->

<!-- A service can have multiple ports. -->
<!-- Each port represents a routable *address*. -->

<!-- A provided service has a target. -->

<!-- ### Ports -->

<!-- ### Addresses -->

<!-- Routers deal in addresses. -->
<!-- An address is service name plus port.  One communication channel.  Each one has a protocol. -->

<!-- ### Protocols -->

<!-- Some protocols work at the granularity of connections.  Each connection is an opaque stream.  Load balancing! -->
<!-- Some protocols work at the granularity of requests (and responses).  Load balancing! -->

## Skupper applications and components

Part of Skupper's job is modeling how a multi-site application works.
To do that, we need to represent important application entities.

An **application** is a set of components.  A **component** is a
logical part of an application.

Our example application is simple.  It has two components: a frontend
and a backend.

~~~
+-------------------------------------------------------------------------+
|                        Application "Hello World"                        |
|                                                                         |
| +-------------------------------+   +---------------------------------+ |
| |      Component "frontend"     |   |        Component "backend"      | |
| +-------------------------------+   +---------------------------------+ |
+-------------------------------------------------------------------------+
~~~

Each component is implemented as a set of **processes**.

~~~
+---------------------------------------------------------------------------+
|                         Application "Hello World"                         |
|                                                                           |
| +---------------------------------+   +---------------------------------+ |
| |       Component "frontend"      |   |        Component "backend"      | |
| |                                 |   |                                 | |
| | +-----------------------------+ |   | +-----------------------------+ | |
| | | Process "site-1/frontend-1" | |   | | Process "central/backend-1" | | |
| | +-----------------------------+ |   | +-----------------------------+ | |
| | +-----------------------------+ |   | +-----------------------------+ | |
| | | Process "site-1/frontend-2" | |   | | Process "central/backend-2" | | |
| | +-----------------------------+ |   | +-----------------------------+ | |
| | +-----------------------------+ |   |                                 | |
| | | Process "site-2/frontend-1" | |   |                                 | |
| | +-----------------------------+ |   |                                 | |
| | +-----------------------------+ |   |                                 | |
| | | Process "site-2/frontend-2" | |   |                                 | |
| | +-----------------------------+ |   |                                 | |
| +---------------------------------+   +---------------------------------+ |
+---------------------------------------------------------------------------+
~~~

Components and processes can span sites.  In the example below, some
processes of the frontend component are running in site "site-1" and
some are running in site "site-2".

~~~
+------------------------------+   +-----------------------------+   +------------------------------+
|         Site "site-1"        |   |        Site "central"       |   |         Site "site-2"        |
|                              |   |                             |   |                              |
| +--------------------------+ |   | +-------------------------+ |   | +--------------------------+ |
| |   Deployment "frontend"  | |   | |   Deployment "backend"  | |   | |   Deployment "frontend"  | |
| |                          | |   | |                         | |   | |                          | |
| | +----------------------+ | |   | | +---------------------+ | |   | | +----------------------+ | |
| | | Process "frontend-1" | | |   | | | Process "backend-1" | | |   | | | Process "frontend-1" | | |
| | +----------------------+ | |   | | +---------------------+ | |   | | +----------------------+ | |
| | +----------------------+ | |   | | +---------------------+ | |   | | +----------------------+ | |
| | | Process "frontend-2" | | |   | | | Process "backend-2" | | |   | | | Process "frontend-2" | | |
| | +----------------------+ | |   | | +---------------------+ | |   | | +----------------------+ | |
| +--------------------------+ |   | +-------------------------+ |   | +--------------------------+ |
+------------------------------+   +-----------------------------+   +------------------------------+
~~~

Because Skupper makes communication transparent to the application,
the location of the running processes is a concern independent of the
application's design.  You can deploy your application workoads to
locations that suit you today, and you can safely change to new
locations later.

### Application

An application is a set of components that work together to do
something useful.  A *distributed* application has components that can
be deployed as separate processes on different machines.  Distributed
applications are often built with a multitier, service-oriented, or
microservices architecture.

Because the application is broken up into isolated components, the
components need a way to communicate and coordinate.

Skupper networks are designed to enable this inter-component
communication across sites.  A Skupper network usually hosts a single
application.

### Component

A component is a logical part of the application.  It has a role (a
set of responsibilities) in achieving the goals of the application.

Components typically have network interfaces so other components can
communicate with them.  That's why components are often referred to as
"services".

Components are implemented by one or more processes.  Components, as
logical elements of the application, are not confined to one site.  A
component can have implementing processes at multiple sites.

### Process

A process represents running application code.
On Kubernetes, a process is a pod.
On Docker or Podman, a process is a container.
On virtual machines or bare metal hosts, a process is a "process".

<!-- XXX A client process, a server process, or (often) both. -->
