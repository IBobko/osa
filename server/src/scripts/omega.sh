echo 1 | sudo -S ls
echo tGTQosyZ2019 | sudo -S openconnect vpn.msk.odin.net --servercert sha256:ea6e7abba14fafa682a7a7e276b9a49f82c62baebe258d79db77bf2d40847996 --user=ibobko --authgroup=ODIN-Remote-Access --passwd-on-stdin -b
sudo xhost +
sudo docker start 30a7eb4b8420

sudo docker exec -it 30a7eb4b8420 bash

# Export Java
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export PATH=${PATH}:${JAVA_HOME}/bin

export NODEJS_HOME=/home/igor/app/node-v10.22.1-linux-x64
export PATH=${PATH}:${NODEJS_HOME}/bin


https://teams.microsoft.com/l/file/540f7680-6d59-43dd-9925-1292786fb46d?tenantId=d78aee32-8f91-4f9e-90ea-fb72965d9d7c&fileType=xlsb&objectUrl=https%3A%2F%2Fingrammicro-my.sharepoint.com%2Fpersonal%2Fivan_shesterikov_ingrammicro_com%2FDocuments%2FMicrosoft%20Teams%20Chat%20Files%2FCLOUDBLUE%20COGS%20%26%20REVENUE_REPORT_YTD%20P03_2020%20v4.xlsb&baseUrl=https%3A%2F%2Fingrammicro-my.sharepoint.com%2Fpersonal%2Fivan_shesterikov_ingrammicro_com&serviceName=p2p&threadId=19:a9a1fdfb-afa5-4a9d-b027-fc224b83f87c_c0165287-4b4b-429b-aa7c-c9b8276f57bc@unq.gbl.spaces&messageId=1601046507018
