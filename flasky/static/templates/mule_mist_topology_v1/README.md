# misty

This topology contains two branch offices branch1 and branch2 and one datacenter datacenter1. Each site has an SSR at the edge. It comprises of below

3 x SSR routers, two acting as branch sites while one is the Hub - WAN Assurance
Each branch has dual connections to Hub. The branch have their lan networks connected to end hosts. The entire topology can be built inside a KVM host using virtualization.

Please refer "Mule_mist_Topology.png" for connection details. Before using Misty to make API calls to Mist, please ensure the physical or virtual topology is built per the diagram. 
If your physical topology has minor differences, the deployment_vars.j2 may be edited accordingly. If you are using additonal variables in deployment_vars.j2, define the values in env.yml accordingly.
The deployment_vars.j2 is a yaml formatted Jinja2 file  that contains various building blocks used by Mist. The way these building blocks (like Networks, Applications) are serialized in deployment_vars.j2 is very much similar to how Mist consumes them. User may refer to Mist API doc to understand this serialization/schema. Please rename the sample_env.yml to env.yml and fill in the details based on your topology. 