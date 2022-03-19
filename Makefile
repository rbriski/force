deploy:
	ssh root@45.56.98.157 "cd ~/force; git pull && git rebase"
	ssh root@45.56.98.157 "cd ~/force; source bin/activate; pip install -r requirements.txt"
	ssh root@45.56.98.157 "systemctl restart force"