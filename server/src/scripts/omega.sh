echo 1 | sudo -S ls
echo tGTQosyZ2019 | sudo -S openconnect vpn.msk.odin.net --servercert sha256:ea6e7abba14fafa682a7a7e276b9a49f82c62baebe258d79db77bf2d40847996 --user=ibobko --authgroup=ODIN-Remote-Access --passwd-on-stdin -b
sudo xhost +
sudo docker start 30a7eb4b8420

sudo docker exec -it 30a7eb4b8420 bash