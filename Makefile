deploy:
	ssh root@${LINODE_IP} "cd ~/force; git pull && git rebase"
	ssh root@${LINODE_IP} "cd ~/force; source bin/activate; pip install -r requirements.txt"
	ssh root@${LINODE_IP} "systemctl restart force"

ssl:
	ssh root@${LINODE_IP} "certbot --nginx -d deanzaforce.club -d www.deanzaforce.club -m ${EMAIL} --agree-tos --no-eff-email"