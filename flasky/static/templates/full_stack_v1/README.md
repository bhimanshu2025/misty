# misty

This topology is a full stack managed via Mist Cloud. It comprises of below


2 x SSR routers, One acting as branch site Edge while other as Hub site Edge - WAN Assurance

2 x Ex-xxxx switches, One acting as fabric network at branch site while other at hub site - Wired Assurance

2 x Mist Access Points, One acting as a wireless network at branch site while other at hub site - Wireless Assurance


Please refer "Full Stack Topology.png" for connection details. Before using Misty to make API calls to Mist, please ensure the physical topology is built per the diagram. 
If your physical topology has minor differences, the deployment_vars.j2 may be edited accordingly. If you are using additonal variables in deployment_vars.j2, define the values in env.yml accordingly.
The deployment_vars.j2 is a yaml formatted Jinja2 file  that contains various building blocks used by Mist. The way these building blocks (like Networks, Applications) are serialized in deployment_vars.j2 is very much similar to how Mist consumes them. User may refer to Mist API doc to understand this serialization/schema. Please rename the sample_env.yml to env.yml and fill in the details based on your topology. 
