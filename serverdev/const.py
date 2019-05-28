_pass_cred = "sshpass -p {password} "
scp_base = _pass_cred + "scp {src_path} {username}@{target}:{dst_path}"
ssh_base = _pass_cred + "ssh -o StrictHostKeyChecking=no {username}@{target} "
WIN32 = 'windows'
LINUX = 'linux'
