# How to use

```bash
# run all, append --check for dry run
ansible-playbook playbook.ansible.yaml -i hosts 
# rotate ssh key
ansible-playbook playbook.ansible.yaml -i hosts.ini --tags=ssh
# init new git repo
ansible-playbook playbook.ansible.yaml -i hosts.ini --tags=init_git --extra-vars='repo_name=test1'

```
