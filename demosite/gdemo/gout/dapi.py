import docker
import ipaddress
import random
import yaml
import json


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
        if 'environment' not in j:
            service_list[0][i]['env'] = []
        if j.has_key('ports'):
            service_list[0][i]['publish'] = j['ports']
        if 'ports' not in j:
            service_list[0][i]['publish'] = []
        service_list[0][i]['hostname'] = i
        service_list[0][i]['name'] = i
    return service_num, service_list


def docker_service_list():
    client = docker.DockerClient(base_url='tcp://192.168.56.101:32775')
    service_list = []
    for i in client.services.list():
        service_list.append({ i.name: i.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image'].split('@sha256')[0]})
    return service_list

def service_map_port(username_service_list, user_docker_file, username_number):
    int_username_docker_min_number = int(username_number) * 100 + 30000
    int_username_docker_max_number = int_username_docker_min_number + 99

    int_username_all_port_set = set()
    for i in range(int_username_docker_min_number, int_username_docker_max_number+1):
        int_username_all_port_set.add(i)

    with open(user_docker_file, 'r') as f:
        output = f.read()
        if output == '':
            pass
        else:
            pre_username_service_list = json.loads(output)
            int_username_used_port_set = set()
            for i in pre_username_service_list:
                for x, y in i.items():
                    if y['status'] == 'enable':
                        if len(y['publish']) != 0:
                            for z in y['publish']:
                                int_username_used_port_set.add(int(z.split(':')[0]))

    available_username_port_set = int_username_all_port_set - int_username_used_port_set

    cur_username_service_list = username_service_list
    for i in cur_username_service_list:
        for x, y in i.items():
            if y['status'] == 'enable':
                if len(y['publish']) != 0:
                    for index, z in enumerate(y['publish']):
                        map_port_set = set()
                        map_port = random.sample(available_username_port_set, 1)[0]
                        str_map_port = str(map_port)
                        map_port_set.add(map_port)
                        available_username_port_set = available_username_port_set - map_port_set
                        y['publish'][index] = str_map_port + ':' + z
                        print str_map_port

    input_list = cur_username_service_list

    with open(user_docker_file, 'w') as f:
        f.write(json.dumps(input_list))

    return cur_username_service_list



test_list = [{'gitlab-text-metric': {'status': 'enable', 'name': 'gitlab-text-metric', 'image': 'gitlab.starmoon.sh:4567/gdemo/gitlab-text-metric:master.1234567890', 'hostname': 'gitlab-text-metric', 'publish': ['8080', '22', '80'], 'env': []}}, {'gitlab-image-analyzer': {'status': 'enable', 'name': 'gitlab-image-analyzer', 'image': 'gitlab.starmoon.sh:4567/gdemo/gitlab-image-analyzer:master.7da13c3d35a6c5831aacf549b0c9c5c0688aa05a', 'hostname': 'gitlab-image-analyzer', 'publish': ['3003', '22', '9090'], 'env': []}}, {'gitlab-image-render': {'status': 'enable', 'name': 'gitlab-image-render', 'image': 'gitlab.starmoon.sh:4567/gdemo/gitlab-image-render:master.52e259387886c577bcf102952c448c3f90dd602b', 'hostname': 'gitlab-image-render', 'publish': [], 'env': ['OSS_URL=gitlab.sh', 'PRIVATE_BUCKET=gitlab-private', 'PUBLIC_BUCKET=gitlab-public']}}]
service_map_port(test_list, '/Users/yshen/Personal/gdemo/demosite/gdemo/gtext/gdev_docker_info', 156)

'''
print str(random.sample(get_available_subnet_set(), 1)[0])

s_num, s_list = yaml_to_service_args()
print s_num
print s_list

print docker_network_list()
print docker_service_list()
'''

