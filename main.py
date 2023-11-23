import ipaddress
from dotenv import load_dotenv

from custom_modules.netbox_connector import NetboxDevice
from snmp import SNMPDevice
import oid.general
from custom_modules.log import logger


class Router:
    def __init__(self, netbox_item):
        self.netbox = netbox_item
        self.arp_table = SNMPDevice.get_network_table(self.netbox.primary_ip.address.split('/')[0], oid.general.arp_mac, 'IP-MAC')

def check_arps(ip):
    # Перебираем роутеры
    for i in router_vms:
        router = Router(i)
        logger.debug(f'ARP-table for {router.netbox.name} was retrieved')
        for i in router.arp_table:
            if i == str(ip).split('/')[0]:
                logger.info(f'There is ARP entry for {ip}')
                return True
    return False

load_dotenv(dotenv_path='.env')
NetboxDevice.create_connection()
NetboxDevice.get_roles()
router_vms = NetboxDevice.get_vms_by_role(role=NetboxDevice.roles['Router'])

desired_ip = input('Enter IP for check: ')
# Проверка корректности введенного IP
try:
    if ipaddress.IPv4Address(desired_ip.strip()):
        pass
except ipaddress.AddressValueError:
    print('Wrong IP')
    exit()

ip_with_prefix = f'{desired_ip}/{NetboxDevice.get_prefix_for_ip(desired_ip).prefix.split("/")[1]}'

ip_in_arp = check_arps(desired_ip)
ip_in_netbox = NetboxDevice.get_netbox_ip(ip_with_prefix, create=False)

print(f'IP in ARPs: {ip_in_arp}')
if ip_in_netbox:
    print(f'IP in Netbox: {ip_in_netbox[0].url.replace('/api', '', 1)}')
else:
    print(f'IP in Netbox: {ip_in_netbox}')
