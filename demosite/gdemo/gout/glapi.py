import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def login_account(username, password):
    URL = 'https://gitlab.starmoon.sh/api/v4/session'
    POST_DATA = {'login': username, 'password': password}

    r = requests.post(URL, data = POST_DATA, verify = False)
    #print r.json()
    login_result = {}
    if r.status_code == 401:
        login_result =  {'login_status': 'failed'}
    elif r.status_code == 201:
        gitlab_username = r.json()['username']
        gitlab_username_private_token = r.json()['private_token']
        gitlab_username_email = r.json()['email']
        login_result = {'login_status': 'success', 'gitlab_username': gitlab_username, 'gitlab_username_private_token': gitlab_username_private_token, 'gitlab_username_email': gitlab_username_email}
    else:
        login_result = {'login_status': 'unknown'}
    return login_result

def list_account_projects(gitlab_username_private_token):
    URL = 'https://gitlab.starmoon.sh/api/v4/projects'
    HTTP_HEADER = {'PRIVATE-TOKEN': gitlab_username_private_token}
    GET_DATA = {'membership': True}

    r = requests.get(URL, headers = HTTP_HEADER, data = GET_DATA, verify = False)
    project_list = []
    for i in r.json():
        project_list.append(i['path_with_namespace'])
    return project_list, str(len(r.json()))

def list_account_commits_for_project(gitlab_username_private_token, gitlab_username_email, project_path_with_namespace):
    branch_list = list_branch_for_project(gitlab_username_private_token, project_path_with_namespace)
    PREFIX_URL = 'https://gitlab.starmoon.sh/api/v4/projects/'
    SUFFIX_URL = '/repository/commits'
    project_path_with_namespace = project_path_with_namespace.replace("/", "%2F")
    URL = PREFIX_URL + project_path_with_namespace + SUFFIX_URL
    HTTP_HEADER = {'PRIVATE-TOKEN': gitlab_username_private_token}

    commit_list = []
    for i in branch_list:
        GET_DATA = {'ref_name': i}
        r = requests.get(URL, headers = HTTP_HEADER, data = GET_DATA, verify = False)
        #print r.json()
    
        for j in r.json():
            if j['committer_email'] == gitlab_username_email:
                commit_list.append({'branch_name': i, 'commit_id': j['short_id'], 'message': j['message'].replace("\n", "").replace("\r", "")})
    return commit_list, str(len(commit_list)), branch_list

def list_branch_for_project(gitlab_username_private_token, project_path_with_namespace):
    PREFIX_URL = 'https://gitlab.starmoon.sh/api/v4/projects/'
    SUFFIX_URL = '/repository/branches'
    project_path_with_namespace = project_path_with_namespace.replace("/", "%2F")
    URL = PREFIX_URL + project_path_with_namespace + SUFFIX_URL
    HTTP_HEADER = {'PRIVATE-TOKEN': gitlab_username_private_token}

    r = requests.get(URL, headers = HTTP_HEADER, verify = False)
    branch_list = []
    for i in r.json():
        branch_list.append(i['name'])
    return branch_list

def list_job_for_project(gitlab_username_private_token, project_path_with_namespace):
    PREFIX_URL = 'https://gitlab.starmoon.sh/api/v4/projects/'
    SUFFIX_URL = '/jobs'
    project_path_with_namespace = project_path_with_namespace.replace("/", "%2F")
    URL = PREFIX_URL + project_path_with_namespace + SUFFIX_URL
    HTTP_HEADER = {'PRIVATE-TOKEN': gitlab_username_private_token}

    r = requests.get(URL, headers = HTTP_HEADER, verify = False)
    job_list = []
    for i in r.json():
        job_list.append({'branch_name': i['ref'], 'commit_id': i['commit']['short_id'], 'job_status': i['status'], 'job_time': i['finished_at']})
    return job_list

def list_merge_request_for_project(gitlab_username_private_token, project_path_with_namespace):
    PREFIX_URL = 'https://gitlab.starmoon.sh/api/v4/projects/'
    SUFFIX_URL = '/merge_requests'
    project_path_with_namespace = project_path_with_namespace.replace("/", "%2F")
    URL = PREFIX_URL + project_path_with_namespace + SUFFIX_URL
    HTTP_HEADER = {'PRIVATE-TOKEN': gitlab_username_private_token}

    r = requests.get(URL, headers = HTTP_HEADER, verify = False)
    return r.json()

def list_docker_image_for_project(username, password, project_path_with_namespace):
    AUTH_URL = 'https://gitlab.starmoon.sh/jwt/auth'
    AUTH_DATA = {'account': username, 'service': 'container_registry', 'scope': 'repository:' + project_path_with_namespace + ':pull'}

    r = requests.get(AUTH_URL, data = AUTH_DATA, auth = (username, password), verify = False)
    token_str = r.json()['token']
    token_str = 'Bearer ' + token_str

    PREFIX_URL = 'https://gitlab.starmoon.sh:4567/v2/'
    SUFFIX_URL = '/tags/list'
    URL = PREFIX_URL + project_path_with_namespace + SUFFIX_URL
    HTTP_HEADER = {'Authorization': token_str}

    r = requests.get(URL, headers = HTTP_HEADER, verify = False)
    image_list = []
    if r.json().has_key('errors'):
        return image_list
    if r.json().has_key('tags') and r.json()['tags'] != None:   
        for i in r.json()['tags']:
            image_list.append({'branch_name': i.split('.')[0], 'commit_id': i.split('.')[1][0:8], 'image_name': i})
    return image_list


#login_result = login_account('gdev', 'FdrrFdrr')
#print login_result
#print list_account_projects(login_result['gitlab_username_private_token'])
#print list_account_commits_for_project(login_result['gitlab_username_private_token'], 'gdev', 'gdemo/gitlab-image-analyzer')
#print list_job_for_project(login_result['gitlab_username_private_token'], 'gdemo/gitlab-image-analyzer')
#print list_docker_image_for_project('gdev', 'FdrrFdrr', 'gdemo/gitlab-text-metric')
#print list_merge_request_for_project(login_result['gitlab_username_private_token'], 'gdemo/gitlab-image-analyzer')


