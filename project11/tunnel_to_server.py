"""
Simple SSH reverse tunnel helper.

Run this on your Windows PC to expose the local backend (localhost:8000)
through your own Linux server as YOUR_SERVER:REMOTE_PORT.

Reads SSH settings from environment variables (e.g. from a .env file
in the project root):

  SSH_TUNNEL_USER         - SSH username
  SSH_TUNNEL_HOST         - SSH host / IP
  SSH_TUNNEL_PASSWORD     - SSH password or key passphrase (optional)
  SSH_TUNNEL_KEY_PATH     - Path to SSH private key (default: looks in ~/.ssh)
  SSH_TUNNEL_REMOTE_PORT  - Remote port on the server (default: 9000)
  SSH_TUNNEL_LOCAL_PORT   - Local backend port (default: 8000)

The script uses Paramiko to establish the tunnel and will automatically
use the password if provided.
"""

import os
import socket
import select
import threading
from dataclasses import dataclass

import paramiko
from dotenv import load_dotenv


@dataclass
class TunnelConfig:
    ssh_user: str
    ssh_host: str
    ssh_password: str = ""
    ssh_key_path: str = ""
    remote_port: int = 9000
    local_port: int = 8000


def load_config_from_env() -> TunnelConfig:
    # Load .env from project root (folder where this script lives)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)

    ssh_user = os.getenv("SSH_TUNNEL_USER", "").strip()
    ssh_host = os.getenv("SSH_TUNNEL_HOST", "").strip()
    ssh_password = os.getenv("SSH_TUNNEL_PASSWORD", "").strip()
    ssh_key_path = os.getenv("SSH_TUNNEL_KEY_PATH", "").strip()
    remote_port = int(os.getenv("SSH_TUNNEL_REMOTE_PORT", "9000"))
    local_port = int(os.getenv("SSH_TUNNEL_LOCAL_PORT", "8000"))

    if not ssh_user or not ssh_host:
        raise RuntimeError(
            "SSH_TUNNEL_USER and SSH_TUNNEL_HOST must be set in .env or environment."
        )

    return TunnelConfig(
        ssh_user=ssh_user,
        ssh_host=ssh_host,
        ssh_password=ssh_password,
        ssh_key_path=ssh_key_path,
        remote_port=remote_port,
        local_port=local_port,
    )


def handler(chan, host, port):
    """
    Handles a single incoming connection on the remote server by
    forwarding it to the local port.
    """
    sock = socket.socket()
    try:
        sock.connect((host, port))
    except Exception as e:
        print(f"Forwarding connection to {host}:{port} failed: {e}")
        return

    print(f"Connected to local {host}:{port}! Forwarding traffic...")
    while True:
        r, w, x = select.select([sock, chan], [], [])
        if sock in r:
            data = sock.recv(1024)
            if len(data) == 0:
                break
            chan.send(data)
        if chan in r:
            data = chan.recv(1024)
            if len(data) == 0:
                break
            sock.send(data)
    chan.close()
    sock.close()


def reverse_forward_tunnel(cfg: TunnelConfig):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"Connecting to {cfg.ssh_host}...")
    try:
        connect_kwargs = {
            "hostname": cfg.ssh_host,
            "username": cfg.ssh_user,
            "allow_agent": True,
        }
        
        if cfg.ssh_key_path:
            print(f"Using SSH key: {cfg.ssh_key_path}")
            connect_kwargs["key_filename"] = cfg.ssh_key_path
            connect_kwargs["look_for_keys"] = False
        else:
            print("Looking for default SSH keys...")
            connect_kwargs["look_for_keys"] = True
        
        # If password is provided, it can be used for key passphrase or fallback auth
        if cfg.ssh_password:
            connect_kwargs["password"] = cfg.ssh_password

        client.connect(**connect_kwargs)
    except Exception as e:
        print(f"Failed to connect to {cfg.ssh_host}: {e}")
        return
    transport = client.get_transport()
    print(f"Adding reverse tunnel: remote {cfg.remote_port} -> local {cfg.local_port}")
    
    try:
        transport.request_port_forward("0.0.0.0", cfg.remote_port)
    except Exception as e:
        print(f"Error requesting port forward on remote port {cfg.remote_port}: {e}")
        client.close()
        return

    print("Tunnel is up! Press Ctrl+C to close.")

    try:
        while True:
            chan = transport.accept(1000)
            if chan is None:
                continue
            thr = threading.Thread(
                target=handler, args=(chan, "localhost", cfg.local_port),
                daemon=True
            )
            thr.start()
    except KeyboardInterrupt:
        print("\nStopping SSH tunnel...")
    finally:
        transport.cancel_port_forward("0.0.0.0", cfg.remote_port)
        client.close()
        print("SSH tunnel closed.")


def main() -> None:
    try:
        cfg = load_config_from_env()
    except RuntimeError as e:
        print(str(e))
        print(
            "Example .env entries:\n"
            "  SSH_TUNNEL_USER=tracker\n"
            "  SSH_TUNNEL_HOST=rmn.pp.ua\n"
            "  SSH_TUNNEL_PASSWORD=your_password_or_passphrase (optional)\n"
            "  SSH_TUNNEL_KEY_PATH=C:/Users/name/.ssh/id_rsa (optional)\n"
            "  SSH_TUNNEL_REMOTE_PORT=9000\n"
            "  SSH_TUNNEL_LOCAL_PORT=8000\n"
        )
        return

    reverse_forward_tunnel(cfg)


if __name__ == "__main__":
    main()


