# misty
Refer this write-up incase you have used misty/README.md to deploy misty project. This doc explains steps to configure and deploy topologies through misty.

>[!Note]
>The tool only configures objects in Mist. Its expected the devices are adopted in Mist already either through whitebox onboarding or through claim code adoption process.

## STEP 1
This doc assumes user has followed steps from misty/README.md to deploy misty project. 

## STEP 2
Chose the type of topology you are planning to build and based on that construct the deployment_vars.j2 file.
There are some topologies that are included with this project located under misty/flasky/static/templates. Each topology has a README.md with some notes in it explaining the topology.
For example: To build a topology referring full_stack_v1, run the below commands
cp misty/flasky/static/templates/full_stack_v1/deployment_vars.j2 misty/flasky/files/
cp misty/flasky/static/templates/full_stack_v1/sample_env.yml misty/flasky/files/env.yml

Edit the misty/flasky/files/env.yml file to enter your Mist credentials.
The env.yml file is specific to topology. It contains Juniper Mist credentials and any variables that are defined in misty/flasky/files/deployment_vars.j2 template.  If env.yml file doesnt exist, you may create it. 

At minimum, the env.yml file should containe below 3 variables. "host" is the mist instance that the user has an account in. "org_id" is the users Organization in the Mist instance while token is the token value from that Organization. The token can be generated under "My Account" in Mist.
'''
host: api.ac2.mist.com
org_id: 0d0f04a5-06cc-4eff-9af1-1asadf25dc25ce
token: gDudTc4FuBVaRYZusdsawZXc8KAgADCobchhp6VMDiUAup3zn23f1YnCXQ9DWhIEuAhJKjCk9vnEAOsSWIP90aNIbwIO2e0FU6
'''

## STEP 3
Once the deployment_vars.j2 and env.yml files are copied(or created) inside misty/flasky/files/ update the env.yml with your mist credentials and any other values that may be specific to your topology.

## STEP 4
Navigate to http://<vm IP>:5000/swagger and reload the data by making the GET call "/api/reload_data" under Generic API's section. This will load the deployment_vars.j2 and env.yml located under misty/flasky/files/

## STEP 5
At this point, you can create Sites, Networks, Applications and the likes in Mist by going through the list of API's OR make the api call "create_all" to create all the objects defined in the 
deployment_vars.j2 file. If for any reason, you need to modify the deployment_vars.j2, just run the "/api/reload_data" api to reload the new template. All operations made through these set of API calls are idenpotent and can be executed multiple times.




