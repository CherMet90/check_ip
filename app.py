import ipaddress
import time
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from functools import lru_cache

from custom_modules.netbox_connector import NetboxDevice
from snmp import SNMPDevice
import oid.general
from custom_modules.log import logger

load_dotenv(dotenv_path='.env')

app = Flask(__name__)

class Router:
    def __init__(self, netbox_item):
        self.netbox = netbox_item
        self.arp_table = self.get_arp_table(self.netbox.primary_ip.address.split('/')[0])

    @staticmethod
    @lru_cache(maxsize=128)
    def get_arp_table(ip_address):
        # Cache expires after 60 seconds 
        ttl = 60
        timestamp = time.time()
        arp_table = SNMPDevice.get_network_table(ip_address, oid.general.arp_mac, 'IP-MAC')
        return arp_table, timestamp

    def is_arp_entry_valid(self):
        arp_table, timestamp = self.arp_table
        return (time.time() - timestamp) < 60

    def refresh_arp_table(self):
        if not self.is_arp_entry_valid():
            self.arp_table = self.get_arp_table.cache_clear()
            self.arp_table = self.get_arp_table(self.netbox.primary_ip.address.split('/')[0])
        logger.debug(f'ARP-table for {self.netbox.name} was refreshed')

def check_arps(ip):
    # Re-establish Netbox connection
    NetboxDevice.create_connection()
    router_vms = NetboxDevice.get_vms_by_role(role=NetboxDevice.roles['Router'])
    
    # Перебираем роутеры
    for router_vm in router_vms:
        router = Router(router_vm)
        logger.debug(f'ARP-table for {router.netbox.name} was retrieved')
        
        router.refresh_arp_table()
        logger.debug(router.arp_table[0])
        for arp_ip in router.arp_table[0]:
            if arp_ip == str(ip).split('/')[0]:
                logger.info(f'There is ARP entry for {ip}')
                return True
    return False

@app.route('/')
def index():
    return render_template('index.html')  # Render the HTML file

@app.route('/check_ip', methods=['POST'])
def check_ip():
    NetboxDevice.create_connection()
    NetboxDevice.get_roles()
    
    data = request.get_json()
    desired_ip = data.get('ip')
    
    if not desired_ip:
        return jsonify({'error': 'No IP provided'}), 400
    try:
        if ipaddress.ip_address(desired_ip.strip()):
            ip_with_prefix = f'{desired_ip}/{NetboxDevice.get_prefix_for_ip(desired_ip).prefix.split("/")[1]}'
            ip_in_netbox = NetboxDevice.get_netbox_ip(ip_with_prefix, create=False)
            
            ip_in_arp = check_arps(desired_ip.strip())
            return jsonify({
                'ip_in_arp': ip_in_arp if ip_in_arp else 'Not found',
                'ip_in_netbox': ip_in_netbox[0].url.replace('http://', 'https://', 1).replace('/api', '', 1) if ip_in_netbox else None,
            })
    except ValueError:
        return jsonify({'error': 'Invalid IP address'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)