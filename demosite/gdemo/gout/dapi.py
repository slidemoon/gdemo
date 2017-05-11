import docker
import ipaddress
import random
import yaml


def docker_network_list():
    client = docker.DockerClient(base_url='tcp://192.168.56.101:32775')
    network_list = []
    for network in client.networks.list():
        network_list.append({'network_name': network.name, 'network_driver': network.attrs['Driver'], 'network_scope': network.attrs['Scope'], 'network_info': network.attrs['IPAM']['Config']})
    return network_list

def docker_network_create(network_name, network_driver):
    name = network_name
    driver = network_driver
    client = docker.DockerClient(base_url='tcp://192.168.56.101:32775')
    subnet_str = str(random.sample(get_available_subnet_set(), 1)[0])
    subnet_gateway = ('.').join(subnet_str.split('.')[0:3]) + '.254'
    ipam_pool = docker.types.IPAMPool(subnet=subnet_str, gateway=subnet_gateway)
    ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
    create_network = client.networks.create(name, driver=driver, ipam=ipam_config)
    network_create_result = name + ' is created'
    return network_create_result, create_network.attrs

def get_available_subnet_set():
    used_subnet_set = set()
    for i in docker_network_list():
        if i['network_info']:
            used_subnet_set.add(ipaddress.ip_network(i['network_info'][0]['Subnet']))

    all_subnet_set = set()
    sum_subnet = ipaddress.ip_network(u'10.0.0.0/16')
    for subnet in sum_subnet.subnets(new_prefix=24):
        all_subnet_set.add(subnet)

    available_subnet_set = all_subnet_set - used_subnet_set
    return available_subnet_set

def yaml_to_service_args():
    stream = file('/Users/yshen/Personal/gdemo/demosite/gdemo/gtext/docker-compose.yml', 'r')
    yaml_dict = yaml.load(stream)
    service_num = len(yaml_dict['services'])
    if service_num == 0:
        return 'No Service'
    service_list = []
    for i, j in yaml_dict['services'].items():
        service_list.insert(0, {i: ''})
        if j.has_key('image'):
            service_list[0][i] = {'image': j['image']}
        if j.has_key('environment'):
            service_list[0][i]['env'] = j['environment']
        if j.has_key('ports'):
            service_list[0][i]['publish'] = j['ports']
        service_list[0][i]['hostname'] = i
        service_list[0][i]['name'] = i
    return service_num, service_list


def docker_service_list():
    client = docker.DockerClient(base_url='tcp://192.168.56.101:32775')
    service_list = []
    for i in client.services.list():
        service_list.append({ i.name: i.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image'].split('@sha256')[0]})
    return service_list

def service_map_port(enable_service_list, user_port_file, username_number):
    int_username_docker_min_number = int(username_number) + 30000
    int_username_docker_max_number = int_username_docker_min_number + 99

    for i in enable_service_list:
        for x, y in i.items():
            if y.has_key('publish'):
                pass




'''
print str(random.sample(get_available_subnet_set(), 1)[0])

s_num, s_list = yaml_to_service_args()
print s_num
print s_list

print docker_network_list()
print docker_service_list()
'''

