import docker

from boltons.socketutils import BufferedSocket

def update_platform():
    client = docker.DockerClient(base_url='tcp://172.17.0.1:2375')

    for container in client.containers.list():
        if "ingram" in container.image.tags[0]:
            socket = container.exec_run("bash", socket=True, stdin=True)
            socket.output._sock.send(b"cd /root/IdeaProjects/osa\n")
            socket.output._sock.send(b"git pull origin unstable\n")

            bf = BufferedSocket(socket.output._sock)
            pass


            while True:
                try:
                    socket.output._sock.settimeout(10)
                    unknown_byte = socket.output._sock.recv(1024)
                    if not unknown_byte:
                        break
                    print(unknown_byte, end='')
                except:
                    break

            socket.output._sock.send(b"/usr/local/apache-maven-3.6.1/bin/mvn clean install -f poa\n")

            while True:
                try:
                    socket.output._sock.settimeout(10)
                    unknown_byte = socket.output._sock.recv(1024)
                    if not unknown_byte:
                        break
                    print(unknown_byte.decode())
                except:
                    break

            # while 1:
            #     # note that os.read does not work
            #     # because it does not TLS-decrypt
            #     # but returns the low-level encrypted data
            #     # one must use "socket.recv" instead
            #     data = socket.output._sock.recv(16384)
            #     if not data: break
            #     print(data)

            socket.output._sock.send(b"exit\n")

    print(client.containers.list())
    # client = paramiko.SSHClient()
    # client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # client.connect(hostname="172.17.0.1", username="igor", password="1")
    # client.exec_command('adduser {}'.format(username))
    # client.close()


if __name__ == "__main__":
    update_platform()
