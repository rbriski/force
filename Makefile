deploy:
	ssh ${LINODE_CONN} "cd ~/force; git pull && git rebase"
	ssh ${LINODE_CONN} "cd ~/force; source bin/activate; pip install -r requirements.txt"
	ssh ${LINODE_CONN} "systemctl restart force"

ssl:
	ssh ${LINODE_CONN} "certbot --nginx -d deanzaforce.club -d www.deanzaforce.club -m ${EMAIL} --agree-tos --no-eff-email"