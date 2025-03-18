# How to use

```bash
# run all, append --check for dry run, declare ANSIBLE_GATHERING=explicit to skip fact gathering
ansible-playbook playbook.ansible.yaml -i hosts 
# rotate ssh key
ansible-playbook playbook.ansible.yaml --tags=ssh
# init new git repo, reboot 
ansible-playbook playbook.ansible.yaml --tags=init_git --extra-vars='repo_name=test1' #--tags=maintanance --extra-vars='reboot_server=true'

```
