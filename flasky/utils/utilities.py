import mistapi
from mistapi.api import v1 as mist
from pprint import pprint
from flask import current_app
import random
import string
import time
import yaml
from jinja2 import Environment, FileSystemLoader, exceptions
from time import sleep

class MistObj():
    def __init__(self):
        self.__load_data()

    def __load_data(self):
        try:
            with open('flasky/files/env.yml', 'r') as f:
                env = yaml.safe_load(f)
            environment = Environment(loader=FileSystemLoader("flasky/files"))
            template = environment.get_template("deployment_vars.j2")
            output = template.render(env)
            # Write source-of-truth to file
            current_app.logger.info("Write source-of-truth to file")
            with open('flasky/files/deployment_vars.yml','w') as f:
                f.write(output)
            # Save source-of-truth as python dict by parsing rendered YAML
            self.DATA = yaml.safe_load(output)
            self.MIST_TOKEN = env['token'] or ''
            self.MIST_USER = env.get('mist_user')
            self.MIST_PASSWORD =  env.get('mist_password')
            self.MIST_HOST = env.get('host')
            self.MIST_ORG_ID = env.get('org_id')
            self.MISTY_ENV = env
            self.data = self.DATA
            self.org_id = self.MIST_ORG_ID 
            self.session = mistapi.APISession(apitoken=self.MIST_TOKEN, host=self.MIST_HOST )
            current_app.logger.debug(self.data)
            self.session.login()
        except exceptions.TemplateSyntaxError as err:
            current_app.logger.exception(f'Failed to parse the jinja2 file. Error is {err}')
        except Exception as err:
            current_app.logger.exception(f'Error is {err}')

    def reload_data(self):
        self.__load_data()

    @staticmethod
    def filter_assets(assets, filter={}):
        if filter == {}:
            return assets
        else:
            items_found = []
            for i in assets:
                match = True
                for key, val in filter.items():
                    if i.get(key) != val:
                        match = False
                if match:
                    items_found.append(i)
            if items_found == []:
                return None
            elif len(items_found) == 1:
                return items_found[0]
            else:
                return items_found  

    def create_sites(self):
        sites_data = self.data['sites']
        created_sites = []
        try:
            sites = mist.orgs.sites.listOrgSites(self.session, org_id=self.org_id).data
            for s in sites_data:
                ## Check to see if the site already exists. If it does, update it
                info = s['info']
                existing = self.filter_assets(sites, filter={'name':info['name']})
                current_app.logger.info(f"Creating Site {s}")
                if existing is None:
                ## If it doesn't, create it
                    site = mist.orgs.sites.createOrgSite(self.session, org_id=self.org_id, body=info).data
                else:
                    current_app.logger.info(f"Site {s} already exists. Updating it.")
                    # to avoid overwriting any existing template assignments, make sure any existing
                    # are preserved
                    # This is not strictly necessary if you have zeroized your organization, but is included
                    # as an example of how you might adapt this script to work with existing org settings.
                    template_keys = [
                        'rftemplate_id',
                        'aptemplate_id',
                        'secpolicy_id',
                        'alarmtemplate_id',
                        'networktemplate_id',
                        'gatewaytemplate_id',
                        'sitetemplate_id'
                    ]
                    for k in template_keys:
                        if existing[k] is not None:
                            info[k]=existing[k]     
                    site = mist.sites.sites.updateSiteInfo(self.session, site_id=existing['id'], body=info).data
                created_sites.append(site)
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return created_sites

    def delete_sites(self):
        deleted_sites = []
        sites_data = self.data['sites']
        try:
            existing_sites = mist.orgs.sites.listOrgSites(self.session, org_id=self.org_id).data
            for s in sites_data:
                ## Check to see if the site already exists. If it does, update it
                info = s['info']
                existing_site = self.filter_assets(existing_sites, filter={'name':info['name']})
                if existing_site:
                    payload = {
                        'rftemplate_id': None,
                        'aptemplate_id': None,
                        'secpolicy_id': None,
                        'alarmtemplate_id': None,
                        'networktemplate_id': None,
                        'gatewaytemplate_id': None,
                        'sitetemplate_id': None
                    }
                    current_app.logger.info(f"Cleaning up potentially dead references from site {existing_site['name']}:{existing_site['id']}")
                    updated = mist.sites.sites.updateSiteInfo(self.session, site_id=existing_site['id'], body=payload)
                    current_app.logger.info(updated.status_code)
                    dead = mist.sites.sites.deleteSite(self.session, site_id=existing_site['id'])
                    current_app.logger.info(dead.status_code)
                    current_app.logger.debug(dead.data)
                    deleted_sites.append(dead.data)
                else:
                    current_app.logger.info(f"Site {info['name']} does not exist in Mist.")
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return ["Successfully Deleted Sites"]

    def create_site_variables(self):
        sites_data = self.data['sites']
        created_sites = []
        try:
            sites = mist.orgs.sites.listOrgSites(self.session, org_id=self.org_id).data
            for s in sites_data:
                current_app.logger.info(f"Creating Site Variables for Site {s['info']['name']} with variables {s['settings']['vars']}")
                existing = self.filter_assets(sites, filter={'name':s['info']['name']})
                settings = s['settings']
                # created the sites in the previous step, so no need to check for existence this time
                site = mist.sites.setting.updateSiteSettings(self.session, site_id=existing['id'], body=settings).data
                created_sites.append(site)
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return created_sites

    def assign_devices(self):
        assigned_devices = []
        sites_data = self.data['sites']
        try:
            sites = mist.orgs.sites.listOrgSites(self.session, org_id=self.org_id).data
            aps = mist.orgs.inventory.getOrgInventory(self.session, org_id=self.org_id, type='ap').data
            switches = mist.orgs.inventory.getOrgInventory(self.session, org_id=self.org_id, type='switch').data
            edges = mist.orgs.inventory.getOrgInventory(self.session, org_id=self.org_id, type='gateway').data
            for s in sites_data:
                assign_site = self.filter_assets(sites, filter={'name':s['info']['name']})
                assignments = s['assignments']
                for e in assignments.get('edges', []):
                    current_app.logger.info(f"Assigning SDWAN Edge {e} to site {s}")
                    payload = {
                        'op':'assign',
                        'managed': True,
                        'macs': [e['mac']],
                        'site_id':assign_site['id']
                    }
                    assignment = mist.orgs.inventory.updateOrgInventoryAssignment(self.session, self.org_id, body=payload).data
                    current_app.logger.info(f"Assignment Result: {assignment}")
                    mac = "".join(e['mac'].split(":"))
                    edge = self.filter_assets(edges, filter={'mac':mac})
                    payload = {'name':e['name']}
                    assigned_device = mist.sites.devices.updateSiteDevice(self.session,  site_id=assign_site['id'], device_id=edge['id'], body=payload).data
                    assigned_devices.append(assigned_device)
                for a in assignments.get('aps', []):
                    current_app.logger.info(f"Assigning Access Point {a} to site {s}")
                    payload = {
                        'op':'assign',
                        'managed': True,
                        'macs': [a['mac']],
                        'site_id':assign_site['id']
                    }
                    assignment = mist.orgs.inventory.updateOrgInventoryAssignment(self.session, self.org_id, body=payload).data
                    current_app.logger.info(f"Assignment Result: {assignment}")
                    mac = "".join(a['mac'].split(":"))
                    ap = self.filter_assets(aps, filter={'mac':mac})
                    payload = {'name':a['name']}
                    assigned_device = mist.sites.devices.updateSiteDevice(self.session,  site_id=assign_site['id'], device_id=ap['id'], body=payload).data
                    assigned_devices.append(assigned_device)
                for sw in assignments.get('switches', []):
                    current_app.logger.info(f"Assigning Switch {sw} to site {s}")
                    payload = {
                        'op':'assign',
                        'managed': True,
                        'macs': [sw['mac']],
                        'site_id':assign_site['id']
                    }
                    assignment = mist.orgs.inventory.updateOrgInventoryAssignment(self.session, self.org_id, body=payload).data
                    current_app.logger.info(f"Assignment Result: {assignment}")
                    mac = "".join(sw['mac'].split(":"))
                    switch = self.filter_assets(switches, filter={'mac':mac})
                    payload = {'name':sw['name']}
                    assigned_device = mist.sites.devices.updateSiteDevice(self.session,  site_id=assign_site['id'], device_id=switch['id'], body=payload).data
                    assigned_devices.append(assigned_device)
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return assigned_devices

    # def unassign_devices(self):
    #     unassigned_devices = []
    #     sites_data = self.data['sites']
    #     try:
    #         aps = mist.orgs.inventory.getOrgInventory(self.session, org_id=self.org_id, type='ap').data
    #         switches = mist.orgs.inventory.getOrgInventory(self.session, org_id=self.org_id, type='switch').data
    #         edges = mist.orgs.inventory.getOrgInventory(self.session, org_id=self.org_id, type='gateway').data
    #         all_devices = aps + switches + edges
    #         for d in all_devices:
    #             payload = {
    #                     'op':'unassign',
    #                     'macs': [d['mac']]
    #                 }
    #             current_app.logger.info(f"Unassigning Device {d['mac']}:{d['id']}")
    #             unassigned = mist.orgs.inventory.updateOrgInventoryAssignment(self.session, org_id=self.org_id, body=payload)
    #             current_app.logger.info(unassigned.data)
    #             unassigned_devices.append(unassigned.data)
    #     except Exception as err:
    #         current_app.logger.exception(f'Error is: {err}')
    #         return f"Error is: {err}"
    #     return unassigned_devices 

    def unassign_devices(self):
        unassigned_devices = []
        sites_data = self.data['sites']
        try:
            # aps = mist.orgs.inventory.getOrgInventory(self.session, org_id=self.org_id, type='ap').data
            # switches = mist.orgs.inventory.getOrgInventory(self.session, org_id=self.org_id, type='switch').data
            # edges = mist.orgs.inventory.getOrgInventory(self.session, org_id=self.org_id, type='gateway').data
            # all_devices = aps + switches + edges
            for s in sites_data:
                assignments = s['assignments']
                for e in assignments.get('edges'):
                    payload = {
                            'op':'unassign',
                            'macs': [e['mac']]
                        }
                    current_app.logger.info(f"Unassigning Device {e['mac']}:{e['name']}")
                    unassigned = mist.orgs.inventory.updateOrgInventoryAssignment(self.session, org_id=self.org_id, body=payload)
                    current_app.logger.info(unassigned.data)
                    unassigned_devices.append(unassigned.data)
                for a in assignments.get('aps'):
                    payload = {
                            'op':'unassign',
                            'macs': [a['mac']]
                        }
                    current_app.logger.info(f"Unassigning Device {a['mac']}:{a['name']}")
                    unassigned = mist.orgs.inventory.updateOrgInventoryAssignment(self.session, org_id=self.org_id, body=payload)
                    current_app.logger.info(unassigned.data)
                    unassigned_devices.append(unassigned.data)
                for sw in assignments.get('switches'):
                    payload = {
                            'op':'unassign',
                            'macs': [sw['mac']]
                        }
                    current_app.logger.info(f"Unassigning Device {sw['mac']}:{sw['name']}")
                    unassigned = mist.orgs.inventory.updateOrgInventoryAssignment(self.session, org_id=self.org_id, body=payload)
                    current_app.logger.info(unassigned.data)
                    unassigned_devices.append(unassigned.data)
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return unassigned_devices 
    
    def create_networks(self):
        net_list = []
        networks = self.data['networks']
        try:
            existing_networks = mist.orgs.networks.listOrgNetworks(self.session, org_id=self.org_id).data
            for net in networks:
                current_app.logger.info(f"Creating Network {net}")
                existing_network = self.filter_assets(existing_networks, filter={'name':net['name']})
                if existing_network is None:
                    new_net = mist.orgs.networks.createOrgNetwork(self.session, org_id=self.org_id, body=net).data
                else:
                    current_app.logger.info(f"Network {net} already exists. Updating Network")
                    new_net = mist.orgs.networks.updateOrgNetwork(self.session, org_id=self.org_id,
                                                                network_id=existing_network['id'], body=net).data
                net_list.append(new_net)
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return net_list

    def delete_networks(self):
        deleted_networks = []
        try:
            networks = self.data['networks']
            existing_networks = mist.orgs.networks.listOrgNetworks(self.session, org_id=self.org_id).data
            # networks = mist.orgs.networks.listOrgNetworks(self.session, org_id=self.org_id).data
            for net in networks:
                existing_network = self.filter_assets(existing_networks, filter={'name':net['name']})
                if existing_network:
                    current_app.logger.info(f"Deleting Network: {existing_network['name']}:{existing_network['id']}")
                    deleted = mist.orgs.networks.deleteOrgNetwork(self.session, org_id=self.org_id, network_id=existing_network['id'])
                    current_app.logger.info(deleted.status_code)
                    deleted_networks.append(deleted.data)
                else:
                    current_app.logger.info(f"Network not deleted: {net['name']}. Reason: Network doesnt exist in Mist")
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return [f"Successfully Deleted Networks {deleted_networks}"]
    
    def create_applications(self):
        apps = self.data['applications']
        created_apps = []
        try:
            existing_apps = mist.orgs.services.listOrgServices(self.session, org_id=self.org_id).data
            for app in apps:
                current_app.logger.info(f"Creating App {app}")
                existing_app = self.filter_assets(existing_apps, filter={'name':app['name']})
                # Check for existing application. Create or update accordingly
                if existing_app is None:
                    new_app = mist.orgs.services.createOrgService(self.session, org_id=self.org_id, body=app).data
                else:
                    current_app.logger.info(f"App {app} already exists in Mist. Updating it")
                    new_app = mist.orgs.services.updateOrgService(self.session, org_id=self.org_id, service_id=existing_app['id'], body=app).data
                created_apps.append(new_app)
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return created_apps

    def delete_applications(self):
        deleted_apps = []
        try:
            apps = self.data['applications']
            existing_apps = mist.orgs.services.listOrgServices(self.session, org_id=self.org_id).data
            for app in apps:
                current_app.logger.info(f"Deleting Application: {app['name']}")
                existing_app = self.filter_assets(existing_apps, filter={'name':app['name']})
                if existing_app:
                    deleted = mist.orgs.services.deleteOrgService(self.session, org_id=self.org_id, service_id=existing_app['id'])
                    current_app.logger.info(deleted.status_code)
                    deleted_apps.append(deleted.data)
                else:
                    current_app.logger.info(f"Application {app['name']} doesnt exist in Mist.")
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return [f"Successfully Deleted Applications {deleted_apps}"]

    def create_vpns(self):
        vpns = self.data['vpns']
        formatted_vpn = {}
        for vpn in vpns:
            formatted_vpn[vpn] = {}
        payload = {
        "name":"OrgOverlay",
        "paths": formatted_vpn,
        "created_by":"user"
        }
        vpn_li = []
        try:
            existing_vpns = mist.orgs.vpns.listOrgVpns(self.session, org_id=self.org_id).data
            # import pdb;pdb.set_trace()
            for vpn in existing_vpns:
                existing_vpn = self.filter_assets(existing_vpns, filter={'name':'OrgOverlay'})
                if existing_vpn is None:
                    ret = mist.orgs.vpns.createOrgVpn(self.session, org_id=self.org_id, body=payload).data
                else:
                    existing_paths =  existing_vpn.get('paths')
                    payload["paths"].update(existing_paths)
                    ret = mist.orgs.vpns.updateOrgVpn(self.session, org_id=self.org_id, vpn_id=existing_vpn['id'], body=payload).data
                vpn_li.append(ret)
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return vpn_li

    def delete_vpns(self):
        vpns = self.data['vpns']
        formatted_vpn = {}
        for vpn in vpns:
            formatted_vpn[vpn] = {}
        payload = {
        "name":"OrgOverlay",
        "paths": formatted_vpn,
        "created_by":"user"
        }
        try:
            existing_vpns = mist.orgs.vpns.listOrgVpns(self.session, org_id=self.org_id).data
            # current_app.logger.info(f"Deleting VPN: {vpn}")
            existing_vpn = self.filter_assets(existing_vpns, filter={'name':'OrgOverlay'})
            if existing_vpn:
                paths = existing_vpn.get('paths')
                for k,v in payload['paths'].items():
                    if k in paths:
                        paths.pop(k)
                existing_vpn['paths'] = paths
                mist.orgs.vpns.updateOrgVpn(self.session, org_id=self.org_id, vpn_id=existing_vpn['id'], body=existing_vpn).data
            else:
                current_app.logger.info(f"VPN OrgOverlay does not exist in Mist.")
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return ["Successfully Deleted VPN's"]
    
    def create_hub_profiles(self):
        hub_profiles = self.data['hub_profiles']
        created_hub_profiles = []
        assigned_hub_profile = []
        try:
            # First, you'll grab lists containing existing hub profiles, sites, and gateway devices respectively.
            existing_hubs = mist.orgs.deviceprofiles.listOrgDeviceProfiles(self.session, org_id=self.org_id, type='gateway').data
            # loop through each hub profile in hub['hub_profiles']
            for hub in hub_profiles:
                current_app.logger.info(f"Creating Hub Profile {hub}")
                # Check for an existing hub profile that matches the one you want to make
                existing_hub = self.filter_assets(existing_hubs, filter={'name':hub['name']})
                # The .pop function serves two purposes here
                # 1. It saves the device and site settings from the hub profile
                # 2. It also removes those keys from the hub dictionary, so they will not ultimately be passed to
                #    the createOrgDeviceProfile() function,  which does not want them
                apply_device = hub.get('device')
                apply_site = hub.get('site')
                if existing_hub is None:
                    new_hub = mist.orgs.deviceprofiles.createOrgDeviceProfile(self.session, org_id=self.org_id, body=hub).data
                else:
                    current_app.logger.info(f"Hub Profile {hub} already exists in Mist. Updating it.")
                    new_hub = mist.orgs.deviceprofiles.updateOrgDeviceProfile(self.session, org_id=self.org_id, deviceprofile_id=existing_hub['id'], 
                                                                            body=hub).data
                created_hub_profiles.append(new_hub)
                # Apply to configured device
                payload = {
                    'macs':[apply_device['mac']]
                }
                updated_device = mist.orgs.deviceprofiles.assignOrgDeviceProfile(self.session, org_id=self.org_id, deviceprofile_id=new_hub['id'],
                                                                                body=payload).data
                assigned_hub_profile.append(updated_device)
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return created_hub_profiles + assigned_hub_profile
        
    def delete_hub_profiles(self):
        deleted_hub_profiles = []
        try:
            hub_profiles = self.data['hub_profiles']
            existing_hubs = mist.orgs.deviceprofiles.listOrgDeviceProfiles(self.session, org_id=self.org_id, type='gateway').data
            for hub in hub_profiles:
                current_app.logger.info(f"Deleting Hub Profile: {hub['name']}")
                payload = {
                    'macs':[]
                }
                existing_hub = self.filter_assets(existing_hubs, filter={'name':hub['name']})
                if existing_hub:
                    updated_device = mist.orgs.deviceprofiles.assignOrgDeviceProfile(self.session, org_id=self.org_id, deviceprofile_id=existing_hub['id'], 
                                                                                    body=payload).data
                    deleted = mist.orgs.deviceprofiles.deleteOrgDeviceProfile(self.session, org_id=self.org_id, deviceprofile_id=existing_hub['id'])
                    deleted_hub_profiles.append(deleted.data)
                    current_app.logger.info(deleted.status_code)
                else:
                    current_app.logger.info(f"Hub profile {hub['name']} does not exist in Mist.")
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return [f"Successfully Deleted Hub Profiles {deleted_hub_profiles}"]
        
    def create_wan_edge_templates(self):
        created_templates = []
        assigned_templates = []
        edge_templates = self.data['wan_edge_templates']
        try:
            existing_edges = mist.orgs.gatewaytemplates.listOrgGatewayTemplates(self.session, org_id=self.org_id).data
            sites = mist.orgs.sites.listOrgSites(self.session, org_id=self.org_id).data
            for edge in edge_templates:
                current_app.logger.info(f"Creating WAN Edge Template {edge}")
                existing_edge = self.filter_assets(existing_edges, filter={'name':edge['name']})
                apply_to = edge.get('sites')
                if existing_edge is None:
                    new_edge = mist.orgs.gatewaytemplates.createOrgGatewayTemplate(self.session, org_id=self.org_id, body=edge).data
                else:
                    current_app.logger.info(f"WAN Edge Template {edge} already exists in Mist. Updating it.")
                    new_edge = mist.orgs.gatewaytemplates.updateOrgGatewayTemplate(self.session, org_id=self.org_id, gatewaytemplate_id=existing_edge['id'], 
                                                                                body=edge).data
                created_templates.append(new_edge)
                # Apply to configured sites.
                for s in apply_to:
                    apply_site = self.filter_assets(sites, filter={'name':s})
                    apply_site['gatewaytemplate_id'] = new_edge['id']
                    updated_site = mist.sites.sites.updateSiteInfo(self.session, site_id=apply_site['id'], body=apply_site).data
                    assigned_templates.append(updated_site)
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return created_templates + assigned_templates
        
    def delete_wan_edge_templates(self):
        deleted_templates = []
        try:
            edge_templates = self.data['wan_edge_templates']
            existing_edges = mist.orgs.gatewaytemplates.listOrgGatewayTemplates(self.session, org_id=self.org_id).data
            for edge in edge_templates:
                current_app.logger.info(f"Deleting WAN Edge Template: {edge['name']}")
                existing_edge = self.filter_assets(existing_edges, filter={'name':edge['name']})
                if existing_edge:
                    deleted = mist.orgs.gatewaytemplates.deleteOrgGatewayTemplate(self.session, org_id=self.org_id, gatewaytemplate_id=existing_edge['id'])
                    current_app.logger.info(deleted.status_code)
                    deleted_templates.append(deleted.data)
                else:
                    current_app.logger.info(f"Wan Edge Template {edge['nam']} does not exist in Mist.")
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return [f"Successfully Deleted WAN Edge Templates: {deleted_templates}"]

    def create_switch_templates(self):
        created_templates = []
        assigned_templates = []
        switch_templates = self.data['switch_templates']
        try:
            existing_sws = mist.orgs.networktemplates.listOrgNetworkTemplates(self.session, org_id=self.org_id).data
            sites = mist.orgs.sites.listOrgSites(self.session, org_id=self.org_id).data
            for sw in switch_templates:
                current_app.logger.info(f"Creating Switch Template {sw}")
                existing_sw = self.filter_assets(existing_sws, filter={'name':sw['name']})
                apply_to = sw.get('sites')
                if existing_sw is None:
                    new_sw = mist.orgs.networktemplates.createOrgNetworkTemplate(self.session, org_id=self.org_id, body=sw).data
                else:
                    current_app.logger.info(f"Switch Template {sw} already exists in Mist. Updating it.")
                    new_sw = mist.orgs.networktemplates.updateOrgNetworkTemplates(self.session, org_id=self.org_id, networktemplate_id=existing_sw['id'], 
                                                                                body=sw).data
                created_templates.append(new_sw)
                # Apply to configured sites.
                for s in apply_to:
                    apply_site = self.filter_assets(sites, filter={'name':s})
                    apply_site['networktemplate_id'] = new_sw['id']
                    updated_site = mist.sites.sites.updateSiteInfo(self.session, site_id=apply_site['id'], body=apply_site).data  
                    assigned_templates.append(updated_site)
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return created_templates + assigned_templates
        
    def delete_switch_templates(self):
        deleted_templates =[]
        try:
            switch_templates = self.data['switch_templates']
            existing_sws = mist.orgs.networktemplates.listOrgNetworkTemplates(self.session, org_id=self.org_id).data
            for sw in switch_templates:
                current_app.logger.info(f"Deleting Switch Template: {sw['name']}")
                existing_sw = self.filter_assets(existing_sws, filter={'name':sw['name']})
                if existing_sw:
                    deleted = mist.orgs.networktemplates.deleteOrgNetworkTemplate(self.session, org_id=self.org_id, networktemplate_id=existing_sw['id'])
                    current_app.logger.info(deleted.status_code)
                    deleted_templates.append(deleted.data)
                else:
                    current_app.logger.info(f"Switch Template {sw['name']} does not exist in Mist.")
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return [f"Successfully Deleted Switch Templates {deleted_templates}"]
    
    def create_wlan_templates(self):
        created_templates = []
        wlan_templates = self.data['wlan_templates']
        try:
            existing_wlan_templates = mist.orgs.templates.listOrgTemplates(self.session, org_id=self.org_id).data
            for w in wlan_templates:
                current_app.logger.info(f"Creating WLAN Template {w}")
                existing_wlan_template = self.filter_assets(existing_wlan_templates, filter={'name':w['name']})
                if existing_wlan_template is None:
                    new_wlan_template = mist.orgs.templates.createOrgTemplate(self.session, org_id=self.org_id, body=w).data
                else:
                    current_app.logger.info(f"WLAN Template {w} already exists in Mist. Updating it.")
                    new_wlan_template = mist.orgs.templates.updateOrgTemplate(self.session, org_id=self.org_id, template_id=existing_wlan_template['id'],
                                                                            body=w).data
                created_templates.append(new_wlan_template)
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return created_templates
                
    def delete_wlan_templates(self):
        deleted_templates = []
        try:
            wlan_templates = self.data['wlan_templates']
            existing_wlan_templates = mist.orgs.templates.listOrgTemplates(self.session, org_id=self.org_id).data
            for w in wlan_templates:
                current_app.logger.info(f"Deleting WLAN Template: {w['name']}")
                existing_wlan_template = self.filter_assets(existing_wlan_templates, filter={'name':w['name']})
                if existing_wlan_template:
                    deleted = mist.orgs.templates.deleteOrgTemplate(self.session, org_id=self.org_id, template_id=existing_wlan_template['id'])
                    current_app.logger.info(deleted.status_code)
                    deleted_templates.append(deleted.data)
                else:
                    current_app.logger.info(f"WLAN Template {w['name']} does not exist in Mist.")
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return [f"Successfully Deleted WLAN Templates {deleted_templates}"]
    
    def create_wlans(self):
        created_wlans = []
        wlans = self.data['wlans']
        try:
            existing_wlans = mist.orgs.wlans.listOrgWlans(self.session, org_id=self.org_id).data
            for wlan in wlans:
                current_app.logger.info(f"Creating WLAN {wlan}")
                existing_wlan = self.filter_assets(existing_wlans, filter={'ssid':wlan['ssid']})
                templates = mist.orgs.templates.listOrgTemplates(self.session, org_id=self.org_id).data
                # The template key in the wlan dictionary tells you which template to attach this to, but should not be included
                # in the payload. You will pop it and use its value in the filter_assets function to select
                # the WLAN template you want to apply to
                template = self.filter_assets(templates, filter={'name':wlan.get('template')})
                # Here you will grab the id value from the selected WLAN template to associate this WLAN
                # with the correct template
                if existing_wlan is None:
                    wlan['template_id'] = template['id']
                    new_wlan = mist.orgs.wlans.createOrgWlan(self.session, org_id=self.org_id, body=wlan).data
                else:
                    current_app.logger.info(f" WLAN {wlan} already exists in Mist. Updating it.")
                    wlan['template_id'] = template['id']
                    new_wlan = mist.orgs.wlans.updateOrgWlan(self.session, org_id=self.org_id, wlan_id=existing_wlan['id'], body=wlan).data
                created_wlans.append(new_wlan)
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return created_wlans
    
    def delete_wlans(self):
        deleted_wlans = []
        try:
            wlans = self.data['wlans']
            existing_wlans = mist.orgs.wlans.listOrgWlans(self.session, org_id=self.org_id).data
            for wlan in wlans:
                current_app.logger.info(f"Deleting WLAN: {wlan['ssid']}")
                existing_wlan = self.filter_assets(existing_wlans, filter={'ssid':wlan['ssid']})
                if existing_wlan:
                    deleted = mist.orgs.wlans.deleteOrgWlan(self.session, org_id=self.org_id, wlan_id=existing_wlan['id'])
                    current_app.logger.info(deleted.status_code)
                    deleted_wlans.append(deleted.data)
                else:
                    current_app.logger.info(f"WLAN {wlan['ssid']} does not exist in Mist.")
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return [f"Successfully Deleted WLAN {deleted_wlans}"]
    
    def create_psks(self):
        created_psks = []
        def random_password(length):
            characters = string.ascii_letters + string.digits
            password = ''.join(random.choice(characters) for i in range(length))
            return password
        psks = self.data['psks']
        try:
            existing_psks = mist.orgs.psks.listOrgPsks(self.session, org_id=self.org_id).data
            for psk in psks:
                existing_psk = self.filter_assets(existing_psks, filter={'name':psk['name']})
                current_app.logger.info(f"Creating PKS {psk}")
                # If no passphrase is configured, assign a random one
                if psk.get('passphrase',None) is None:
                    psk['passphrase'] = random_password(12)
                # The input data will specify and expiry_time in days, but this key should not be
                # included in the payload. Here you calculate the expire time and remove the expiry_data
                # key with .pop() in one step
                psk['expire_time'] = time.time()+(60*60*24*psk.get('expiry_days'))
                # Create a new PSK if a matching name isn't found, otherwise update the existing key
                if existing_psk is None:
                    new_psk = mist.orgs.psks.createOrgPsk(self.session, org_id=self.org_id, body=psk).data
                else:
                    current_app.logger.info(f"PKS {psk} already exists in Mist. Updating it.")
                    new_psk = mist.orgs.psks.updateOrgPsk(self.session, org_id=self.org_id, psk_id=existing_psk['id'], body=psk).data
                created_psks.append(new_psk)
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return created_psks
    
    def delete_psks(self):
        deleted_psks = []
        try:
            psks = self.data['psks']
            existing_psks = mist.orgs.psks.listOrgPsks(self.session, org_id=self.org_id).data
            for psk in psks:
                current_app.logger.info(f"Deleting PSK: {psk['name']}")
                existing_psk = self.filter_assets(existing_psks, filter={'name':psk['name']})
                if existing_psk:
                    deleted = mist.orgs.psks.deleteOrgPsk(self.session, org_id=self.org_id, psk_id=existing_psk['id'])
                    current_app.logger.info(deleted.status_code)
                    deleted_psks.append(deleted.data)
                else:
                    current_app.logger.info(f"PSK {psk['name']} does not exist in Mist.")
        except Exception as err:
            current_app.logger.exception(f'Error is: {err}')
            return f"Error is: {err}"
        return [f"Successfully Deleted PSKS {deleted_psks}"]

    def create_all(self):
        a = self.create_sites()
        sleep(1)
        b = self.create_site_variables()
        sleep(1)
        c = self.assign_devices()
        sleep(1)
        d = self.create_networks()
        sleep(1)
        e = self.create_applications()
        sleep(1)
        f = self.create_vpns()
        sleep(1)
        g = self.create_hub_profiles()
        sleep(1)
        h = self.create_wan_edge_templates()
        sleep(1)
        i = self.create_switch_templates()
        sleep(1)
        j = self.create_wlan_templates()
        sleep(1)
        k = self.create_wlans()
        sleep(1)
        l = self.create_psks()
        sleep(1)
        return [a] + [b] + [c] + [d] + [e] + [f] + [g] + [h] + [i] + [j] + [k] + [l]

    def delete_all(self):
        a = self.delete_psks()
        sleep(1)
        b = self.delete_wlans()
        sleep(1)
        c = self.delete_wlan_templates()
        sleep(1)
        d = self.delete_switch_templates()
        sleep(1)
        e = self.delete_wan_edge_templates()
        sleep(1)
        f = self.delete_hub_profiles()
        sleep(1)
        g = self.delete_vpns()
        sleep(1)
        h = self.delete_networks()
        sleep(1)
        i = self.delete_applications()
        sleep(1)
        j = self.unassign_devices()
        sleep(1)
        k = self.delete_sites()
        sleep(1)
        return a + b + c + d + e + f + g + h + i + j + k