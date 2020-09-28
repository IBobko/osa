import paramiko


def get_stack_host(stack_name):
    pass


def snapshot(stack_hash, name, action):
    k = paramiko.RSAKey.from_private_key_file("./data/id_rsa")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname="honey.int.zone", username="root", pkey=k)
    stdin, stdout, stderr = client.exec_command(
        "./dgorodnichev/snapshot.py --name {} --{} {}".format(stack_hash, action, name))
    return stderr.readlines()


def prepare_stack(stack_host):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=stack_host, username="root", password="1q2w3e")
    stdin, stdout, stderr = client.exec_command(
        "sed -i 's/DEBUG_MODE=\"${DEBUG:-false}\"/DEBUG_MODE=\"${DEBUG:-true}\"/' /usr/local/pem/wildfly-16.0.0.Final/bin/standalone.sh")
    print(stdout.readlines())
    stdin, stdout, stderr = client.exec_command(
        "sed -i 's/address=$DEBUG_PORT/address=*:$DEBUG_PORT/' /usr/local/pem/wildfly-16.0.0.Final/bin/standalone.sh")
    print(stdout.readlines())
    stdin, stdout, stderr = client.exec_command("systemctl daemon-reload")
    print(stdout.readlines())
    stdin, stdout, stderr = client.exec_command("/usr/local/pem/wildfly-16.0.0.Final/bin/add-user.sh --user")
    print(stdout.readlines())
    stdin, stdout, stderr = client.exec_command("service pau restart")
    print(stdout.readlines())
    client.close()


# prepare_stack("POAMN-2e2b5a26ae64.aqa.int.zone")
print(snapshot("a43636932874", "igor-igor", "create"))
