from django.shortcuts import render
from django.http import HttpResponse

from gout import glapi, dapi
import os.path
import re

# Create your views here.

def login(request):
    return render(request, 'gdemo/login.html')

def logout(request):
    request.session.flush()
    return HttpResponse('logout')

def main(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        login_status = glapi.login_account(username, password)
        if login_status['login_status'] == 'failed':
            return HttpResponse('failed')
        elif login_status['login_status'] == 'success':
            request.session['gitlab_username'] = login_status['gitlab_username']
            request.session['gitlab_username_private_token'] = login_status['gitlab_username_private_token']
            request.session['gitlab_password'] = request.POST['password']
            request.session['gitlab_username_email'] = login_status['gitlab_username_email']
            account_project_list, account_project_num = glapi.list_account_projects(login_status['gitlab_username_private_token'])
            content = {'account_project_num': account_project_num, 'account_project_list': account_project_list}
            return render(request, 'gdemo/main.html', content)
        elif login_status['login_status'] == 'unknown':
            return  HttpResponse('unknown')
    elif request.method == 'GET':
        account_project_list, account_project_num = glapi.list_account_projects(request.session['gitlab_username_private_token'])
        content = {'account_project_num': account_project_num, 'account_project_list': account_project_list}
        return render(request, 'gdemo/main.html', content)

def gproject(request):
    if 'project_path_with_namespace' not in request.GET:
        account_project_list, account_project_num = glapi.list_account_projects(request.session['gitlab_username_private_token'])
        content = {'account_project_list': account_project_list}
        return render(request, 'gdemo/project.html', content)
    elif 'project_path_with_namespace' in request.GET:
        project_path_with_namespace = request.GET['project_path_with_namespace']
        account_project_list, account_project_num = glapi.list_account_projects(request.session['gitlab_username_private_token'])
        account_commit_list, account_commit_num, branch_list = glapi.list_account_commits_for_project(request.session['gitlab_username_private_token'], request.session['gitlab_username_email'], project_path_with_namespace)
        job_list = glapi.list_job_for_project(request.session['gitlab_username_private_token'], project_path_with_namespace)
        for index, i in enumerate(account_commit_list):
            for j in job_list:
                if j['commit_id'] == i['commit_id']:
                    if account_commit_list[index].has_key('job_status'):
                        pass
                    else:
                        account_commit_list[index]['job_status'] = j['job_status']
                        account_commit_list[index]['job_time'] = j['job_time']
        image_list = glapi.list_docker_image_for_project(request.session['gitlab_username'], request.session['gitlab_password'], project_path_with_namespace)
        for index, i in enumerate(account_commit_list):
            for j in image_list:
                if j['commit_id'] == i['commit_id']:
                    account_commit_list[index]['docker_image'] = 'deploy'
        content = {'account_project_list': account_project_list, 'account_commit_list': account_commit_list}
        return render(request, 'gdemo/project.html', content)

def ddeploy(request):    
    default_service_num, default_service_list = dapi.yaml_to_service_args()
    docker_service_list = dapi.docker_service_list()
    gitlab_username = request.session['gitlab_username']
    print '######## default_service_list %s' % str(default_service_list)
    print '######## docker_service_list %s' % str(docker_service_list)
    default_service_name_list = []
    for i in default_service_list:
        for j in i:
            default_service_name_list.append(j)
    print '######## default_service_name_list %s' % str(default_service_name_list)
    check_gitlab_service_name_list = []
    for i in default_service_name_list:
        check_gitlab_service_name_list.append(gitlab_username + '_' + i)
    print '######## check_gitlab_service_name_list %s' % str(check_gitlab_service_name_list)
    gitlab_service_status_list = []
    gitlab_service_status_list_2 = []
    for i in check_gitlab_service_name_list:
        for j in docker_service_list:
            if j.has_key(i):
                gitlab_service_status_list.append({'service_name': i, 'status': 'enable', 'image': j[i]})
                gitlab_service_status_list_2.append({i.replace(gitlab_username+'_', ''): {'status': 'enable', 'image': j[i]}})
                break
        else:
            gitlab_service_status_list.append({'service_name': i, 'status': 'disable', 'image': '-'})
            gitlab_service_status_list_2.append({i.replace(gitlab_username+'_', ''): {'status': 'disable', 'image': '-'}})
    print '######## gitlab_service_status_list %s' % str(gitlab_service_status_list)
    print '######## gitlab_service_status_list_2 %s' % str(gitlab_service_status_list_2)

    account_project_list, account_project_num = glapi.list_account_projects(request.session['gitlab_username_private_token'])
    for i in default_service_list:
        for x, y in i.items():
            for z in gitlab_service_status_list_2:
                if z.has_key(x):
                    z.values()[0]['stable_image'] = i.values()[0]['image'].replace('gitlab.starmoon.sh:4567/gdemo/'+x+':', '')
    print '######## new_gitlab_service_status_list_2 %s' % str(gitlab_service_status_list_2)
    for i in default_service_name_list:
        match_project_path_with_namespace = [ s for s in account_project_list if i in s]
        print '######## match_project_path_with_namespace %s' % str(match_project_path_with_namespace)
        if match_project_path_with_namespace:
            available_image_list = glapi.list_docker_image_for_project(request.session['gitlab_username'], request.session['gitlab_password'], match_project_path_with_namespace[0])
            print '######## available_image_list %s' % str(available_image_list)
            for z in gitlab_service_status_list_2:
                available_image_list_2 = []
                for j in available_image_list:
                    available_image_list_2.append(j['image_name'])
                if z.has_key(i):
                    z.values()[0]['available_image'] = available_image_list_2
            print '######## available_image_list_2 %s' % str(available_image_list_2)
            print '######## new_2_gitlab_service_status_list_2 %s' % str(gitlab_service_status_list_2)
    if request.method == 'GET':
        gitlab_service_status_list_3 = gitlab_service_status_list_2
        for i, j in enumerate(gitlab_service_status_list_3):
            for m, n in j.items():
                if n['image'] != '-':
                    n['image'] = n['image'].split(':')[2]

        #content = { 'default_service_list': default_service_list, 'docker_service_list': docker_service_list, 'gitlab_service_status_list': gitlab_service_status_list, 'gitlab_service_status_list_3': gitlab_service_status_list_3 }
        content = { 'gitlab_service_status_list_3': gitlab_service_status_list_3 }
        return render(request, 'gdemo/deploy.html', content)
    elif request.method == 'POST':
        docker_network_list =  dapi.docker_network_list()
        username_network_name = gitlab_username + '_docker_network'
        for i in docker_network_list:
            if i['network_name'] == username_network_name:
                username_number = i['network_info'][0]['Gateway'].split('.')[2]
                break
        else:
            x, y = dapi.docker_network_create(username_network_name, 'overlay')
            username_number = y['IPAM']['Config'][0]['Gateway'].split('.')[2]

        username_docker_file_name = 'gtext/' + gitlab_username + '_docker_info'
        username_docker_file = os.path.join(os.path.dirname(__file__), username_docker_file_name)
        if os.path.isfile(username_docker_file):
            pass
        else:
            create_file = open(username_docker_file, 'w')
            create_file.close()

        user_deploy_service_list = []
        for i in gitlab_service_status_list_2:
            for x, y in i.items():
                for m, n in request.POST.items():
                    if x in m and str(m).endswith('_switch'):
                        if y['status'] == 'disable':
                            if n == 'disable':
                                use_image = 'gitlab.starmoon.sh:4567/gdemo/' + x + ':' + y['stable_image']
                                use_docker_name = gitlab_username + '_' + x
                                user_deploy_service_list.append({x: {'action': 'nothing', 'image': use_image, 'hostname': use_docker_name, 'name': use_docker_name}})
                            elif n == 'enable':
                                for a, b in request.POST.items():
                                    b = re.sub(r'\(.*\)', '', b)
                                    if x in a and str(a).endswith('_image'):
                                        if b == '-':
                                            use_image = 'gitlab.starmoon.sh:4567/gdemo/' + x + ':' + y['stable_image']
                                            use_docker_name = gitlab_username + '_' + x
                                            user_deploy_service_list.append({x: {'action': 'start', 'image': use_image, 'hostname': use_docker_name, 'name': use_docker_name}})
                                        else:
                                            use_image = 'gitlab.starmoon.sh:4567/gdemo/' + x + ':' + b
                                            use_docker_name = gitlab_username + '_' + x
                                            user_deploy_service_list.append({x: {'action': 'start', 'image': use_image, 'hostname': use_docker_name, 'name': use_docker_name}})
                        elif y['status'] == 'enable':
                            if n =='disable':
                                use_image = 'gitlab.starmoon.sh:4567/gdemo/' + x + ':' + y['stable_image']
                                use_docker_name = gitlab_username + '_' + x
                                user_deploy_service_list.append({x: {'action': 'stop', 'image': use_image, 'hostname': use_docker_name, 'name': use_docker_name}})
                            elif n == 'enable':
                                for a, b in request.POST.items():
                                    b = re.sub(r'\(.*\)', '', b)
                                    if x in a and str(a).endswith('_image'):
                                        if y['image'] != b:
                                            use_image = 'gitlab.starmoon.sh:4567/gdemo/' + x + ':' + b
                                            use_docker_name = gitlab_username + '_' + x
                                            user_deploy_service_list.append({x: {'action': 'update', 'image': use_image, 'hostname': use_docker_name, 'name': use_docker_name}})
                                        elif y['image'] == b:
                                            use_image = 'gitlab.starmoon.sh:4567/gdemo/' + x + ':' + y['stable_image']
                                            se_docker_name = gitlab_username + '_' + x
                                            user_deploy_service_list.append({x: {'action': 'nothing', 'image': use_image, 'hostname': use_docker_name, 'name': use_docker_name}})
        print  '&&&&&&&& user_deploy_service_list %s' % user_deploy_service_list

        for i in default_service_list:
            for x, y in i.items():
                for z in user_deploy_service_list:
                    for m, n in z.items():
                        if x == m:
                            n['publish'] = y['publish']
                            n['env'] = y['env']
        print  '&&&&&&&& new_user_deploy_service_list %s' % user_deploy_service_list

        username_service_list = user_deploy_service_list

        cur_username_service_list = dapi.service_map_port(username_service_list, username_docker_file, username_number, gitlab_username)

        print '&&&&&&&& cur_username_service_list %s' % cur_username_service_list

        dapi.deploy_docker(cur_username_service_list, username_network_name)

        content = { 'default_service_list': default_service_list, 'docker_service_list': docker_service_list, 'gitlab_service_status_list': gitlab_service_status_list, 'gitlab_service_status_list_2': gitlab_service_status_list_2 }
        return render(request, 'gdemo/deploy.html', content)





















'''
def ddeployback(request):
    default_service_num, default_service_list = dapi.yaml_to_service_args()
    docker_service_list = dapi.docker_service_list()
    gitlab_username = request.session['gitlab_username']
    default_service_name_list = []
    for i in default_service_list:
        for j in i:
            default_service_name_list.append(j)
    check_gitlab_service_name_list = []
    for i in default_service_name_list:
        check_gitlab_service_name_list.append(gitlab_username + '_' + i)
    gitlab_service_status_list = []
    gitlab_service_status_list_2 = []
    for i in check_gitlab_service_name_list:
        for j in docker_service_list:
            if j.has_key(i):
                gitlab_service_status_list.append({'service_name': i, 'status': 'enable', 'image': j[i]})
                gitlab_service_status_list_2.append({i.replace(gitlab_username+'_', ''): {'status': 'enable', 'image': j[i]}})
                break
        else:
            gitlab_service_status_list.append({'service_name': i, 'status': 'disable', 'image': '-'})
            gitlab_service_status_list_2.append({i.replace(gitlab_username+'_', ''): {'status': 'disable', 'image': '-'}})

    account_project_list, account_project_num = glapi.list_account_projects(request.session['gitlab_username_private_token'])
    for i in default_service_list:
        for x, y in i.items():
            for z in gitlab_service_status_list_2:
                if z.has_key(x):
                    z.values()[0]['stable_image'] = i.values()[0]['image'].replace('gitlab.starmoon.sh:4567/gdemo/'+x+':', '')
    for i in default_service_name_list:
        match_project_path_with_namespace = [ s for s in account_project_list if i in s]
        if match_project_path_with_namespace:
            available_image_list = glapi.list_docker_image_for_project(request.session['gitlab_username'], request.session['gitlab_password'], match_project_path_with_namespace[0])
            for z in gitlab_service_status_list_2:
                available_image_list_2 = []
                for j in available_image_list:
                    available_image_list_2.append(j['image_name'])
                if z.has_key(i):
                    z.values()[0]['available_image'] = available_image_list_2
    if request.method == 'POST':
        docker_network_list =  dapi.docker_network_list()
        username_network_name = gitlab_username + '_docker_network'
        for i in docker_network_list:
            if i['network_name'] == username_network_name:
                username_number = i['network_info'][0]['Gateway'].split('.')[2]
                break
        else:
            x, y = dapi.docker_network_create(username_network_name, 'overlay')
            username_number = y['IPAM']['Config'][0]['Gateway'].split('.')[2]

        username_docker_file_name = 'gtext/' + gitlab_username + '_docker_info'
        username_docker_file = os.path.join(os.path.dirname(__file__), username_docker_file_name)
        if os.path.isfile(username_docker_file):
            pass
        else:
            create_file = open(username_docker_file, 'w')
            create_file.close()

        username_service_list = []
        for i in default_service_list:
            for x, y in i.items():
                for z in gitlab_service_status_list_2:
                    for m, n in z.items():
                        if x == m:
                            username_service_list.append({x: {'status': n['status'], 'publish': y['publish'], 'image': y['image'], 'hostname': y['hostname'], 'name': y['name'], 'env': y['env']}})

        for i in username_service_list:
            for x, y in i.items():
                for m, n in request.POST.items():
                    if x in m and str(m).endswith('_switch'):
                        y['status'] = str(n)
                    if x in m and str(m).endswith('_image') and n != u'-':
                        y['image'] = str(n)

        cur_username_service_list = dapi.service_map_port(username_service_list, username_docker_file, username_number, gitlab_username)
        print cur_username_service_list

        dapi.deploy_docker(cur_username_service_list, username_network_name)

        content = { 'default_service_list': default_service_list, 'docker_service_list': docker_service_list, 'gitlab_service_status_list': gitlab_service_status_list, 'gitlab_service_status_list_2': gitlab_service_status_list_2 }

    return render(request, 'gdemo/deployback.html')
'''        
















