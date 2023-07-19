# Skupper terminology

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

In this example, site "west" and site "east" are linked to form the
network for the "Hello World" application.

~~~
+--------------------------------------------+
|            Network "Hello World"           |
|                                            |
| +-------------+            +-------------+ |
| | Site "west" |--- Link ---| Site "east" | |
| +-------------+            +-------------+ |
+--------------------------------------------+
~~~

To create a link, the site that is to be the target of the link must
have a point of ingress, so it can accept a TCP connection.

In this example, site "west" accepts incoming TCP connections through
its ingress, and site "east" creates the site-to-site link by
establishing an outbound TCP connection to "west".

~~~
+-----------------------------------------+
|           Network "Hello World"         |
|                                         |
| +---------------+       +-------------+ |
| |  Site "west"  |       | Site "east" | |
| |               |       |             | |
| |  +---------+  |       |  +-------+  | |
| |  | Ingress |<------------| Link  |  | |
| |  +---------+  |       |  +-------+  | |
| +---------------+       +-------------+ |
+-----------------------------------------+
~~~

Creating a link requires explicit permission from the target site.
This permission is granted using **tokens**.  A token contains a URL
for the target site and a secret key.

In this example, site "west" wishes to allow "east" to create a link.
Site "west" creates a token.  The owner of "west" gives the token to
the owner of "east".  The owner of "east" then uses the token to
create the link.

~~~
  +-------------+             +-------------+
  | Site "west" |             | Site "east" |
  +-------------+             +-------------+
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

Skupper works on multiple platforms: Kubernetes, Podman, virtual
machines, and bare metal hosts.  Each site in a network can run on any
supported platform.

~~~
+---------------------------+      +------------------------+      +-------------------------+
|    Kubernetes cluster     |      |         Podman         |      |     VM or bare metal    |
|                           |      |                        |      |                         |
|  +---------------------+  |      |  +------------------+  |      |  +-------------------+  |
|  |     Site "west":    |  |      |  |  Site "central"  |  |      |  |    Site "east"    |  |
|  |                     |  |      |  |                  |  |      |  |                   |  |
|  |   Namespace "west"  |--- Link ---|  Podman network  |--- Link ---|    Local user     |  |
|  |                     |  |      |  |    "skupper"     |  |      |  |                   |  |
|  +---------------------+  |      |  +------------------+  |      |  +-------------------+  |
+---------------------------+      +------------------------+      +-------------------------+
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
Kubernetes namespaces, Podman hosts including virtual machines and bare metal environments.

### Link

A link is a site-to-site TCP communication channel.  Links serve as a
transport for application traffic such as connections and requests.
Links are always encrypted using mutual TLS.

### Token

A token is required to create a link.  The token contains a URL, which
locates the ingress of the target site, and a secret, which represents
the authority to create the link.

Tokens can be restricted to a chosen number of uses inside a limited
time window.  By default, tokens allow only one use and expire after
15 minutes.

## Skupper listeners and connectors

Site-to-site links are distinct from service-to-service connections.
Links enable site-to-site communication, you create service connections on top of this transport to enable components of your distributed application to communicate.

In this example, sites "west" and "east" have links to site "central".
Workload "frontend" is running on "west", and workload "backend" on
"east".  When "frontend" connects to "backend", it can ignore the
underlying link topology.  Skupper ensures that "frontend" can connect
directly to "backend".

~~~
Service connection    +---------------------+                              +--------------------+
layer                 | Workload "frontend" |-------- Connection --------->| Workload "backend" |
                      +---------------------+                              +--------------------+
                                |                                                    |
-------------------------------------------------------------------------------------------------
                                |                                                    |
Site link layer          +-------------+          +----------------+          +-------------+
                         | Site "west" |-- Link ->| Site "central" |<- Link --| Site "east" |
                         +-------------+          +----------------+          +-------------+
~~~

**Listeners** and **connectors** work together to route service
connections across the network.  

* Listeners provide a local connection endpoint for remote services.  
* Connectors specify the local processes that handle remote service connections.

Listeners and connectors are coupled by matching **routing keys**.
Connections to a listener with a given routing key are forwarded to
remote connectors with the same routing key.

In site "west", workload "frontend" needs to connect to
`backend:8080`.  Skupper provides a local connection listener for that
host and port.

In "east", "backend" is running and ready to handle requests.  Skupper
provides a local connector associated with the processes implementing
"backend".

When "frontend" in "west" connects to the listener, Skupper uses the
routing key to forward the connection data to the matching connector
in "east", which then connects to the "backend" workload.

~~~
+-------------------------------+                        +--------------------------------+
|          Site "west"          |                        |           Site "east"          |
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

~~~
              +-------------------------------------------------------------------------+
              |                        Application "Hello World"                        |
              |                                                                         |
              | +-------------------------------+   +---------------------------------+ |
              | |      Component "frontend"     |   |        Component "backend"      | |
              | +-------------------------------+   +---------------------------------+ |
              +-------------------------------------------------------------------------+

              +-------------------------------------------------------------------------+
              |                        Application "Hello World"                        |
              |                                                                         |
              | +-------------------------------+   +---------------------------------+ |
              | |      Component "frontend"     |   |        Component "backend"      | |
              | |                               |   |                                 | |
              | | +---------------------------+ |   | +-----------------------------+ | |
              | | | Process "west/frontend-1" | |   | | Process "central/backend-1" | | |
              | | +---------------------------+ |   | +-----------------------------+ | |
              | | +---------------------------+ |   | +-----------------------------+ | |
              | | | Process "west/frontend-2" | |   | | Process "central/backend-2" | | |
              | | +---------------------------+ |   | +-----------------------------+ | |
              | | +---------------------------+ |   |                                 | |
              | | | Process "east/frontend-1" | |   |                                 | |
              | | +---------------------------+ |   |                                 | |
              | | +---------------------------+ |   |                                 | |
              | | | Process "east/frontend-2" | |   |                                 | |
              | | +---------------------------+ |   |                                 | |
              | +-------------------------------+   +---------------------------------+ |
              +-------------------------------------------------------------------------+

+------------------------------+   +-----------------------------+   +------------------------------+
|          Site "west"         |   |        Site "central"       |   |          Site "east"         |
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

### Application

An application (a *distributed* application) is a set of components
that work together to do something useful.  Examples are applications
built with database-backed, service-oriented, or microservices
architectures.

Because the application is broken up into isolated components, the
components need a way to communicate and coordinate.

Skupper networks are designed to enable this inter-component
communication across sites.  Skupper networks usually host a single
application.

### Component

A component is a logical element of the application.  It has a role (a
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
On bare-metal hosts or VMs, a process is a "process".
