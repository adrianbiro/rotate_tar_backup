# How to use

```bash
# run all
ansible-playbook playbook.yaml -i hosts 
# rotate ssh key
ansible-playbook playbook.yaml -i hosts --tags=ssh
# init new git repo
ansible-playbook playbook.yaml -i hosts --tags=init_git --extra-vars='repo_name=test1'

```
