"""
Import as:

import helpers.hsftp as hsftp
"""

import logging
import os
import subprocess
import sys
from io import BytesIO
from typing import List

import helpers.henv as henv

henv.install_module_if_not_present("pysftp")

import pysftp

import helpers.haws as haws
import helpers.hsecrets as hsecret

# Create a logger instance.
_LOG = logging.getLogger(__name__)


def check_lftp_connection():
    """
    Check if `lftp` is installed.

    If not, install it using the package manager.
    """
    try:
        # Check if `lftp` is available by trying to run it.
        subprocess.run(
            ["lftp", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _LOG.info("`lftp` is already installed.")
    except subprocess.CalledProcessError:
        _LOG.error("Error occurred while checking `lftp` version.")
        sys.exit(1)
    except FileNotFoundError:
        _LOG.warning("`lftp` is not installed. Attempting to install it...")
        install_lftp()


def install_lftp():
    """
    Install `lftp` using the system package manager.
    """
    try:
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-y", "lftp"], check=True)
        _LOG.info("`lftp` successfully installed using `apt`.")
    except Exception as e:
        _LOG.error("Failed to install `lftp`: %s", e)
        sys.exit(1)


def download_file_using_lftp(
    remote_data_path: str, save_path: str, hostname: str, secret_name: str
) -> None:
    """
    Download files from a remote SFTP server using `lftp` and a private SSH
    key.

    :param remote_data_path: path to the remote directory on the SFTP
        server from which files should be downloaded.
    :param save_path: local directory where the downloaded files will be
        saved.
    :param hostname: hostname of the SFTP server.
    :param secret_name: Name of the secret in AWS Secrets Manager that
        stores the SFTP credentials, including the username and private
        key.
    :return: None.
    """
    # Fetch the private key from AWS Secrets Manager
    secret_dict = hsecret.get_secret(secret_name)
    username = secret_dict["username"]
    private_key = secret_dict["private_key"]
    # Write the private key to a temporary file
    with open("/tmp/temp_key.pem", "w") as temp_key_file:
        temp_key_file.write(private_key)
    # Ensure the key file has the correct permissions
    os.chmod("/tmp/temp_key.pem", 0o600)
    private_key_path = "/tmp/temp_key.pem"
    # Construct the lftp command.
    # The 'set sftp:connect-program' allows specifying custom SSH options for the SFTP connection.
    # -o GSSAPIAuthentication=no: Disables GSSAPI to avoid unnecessary authentication mechanisms.
    # -o StrictHostKeyChecking=no: Bypasses the host key verification prompt for new hosts.
    # -a: Enables SSH agent forwarding for more seamless authentication.
    # -x: Disables X11 forwarding (not needed for file transfer).
    # -i {private_key_path}: Specifies the private key for SSH authentication.
    # 'mirror --parallel=10': Downloads files from the remote server, with 10 parallel downloads to speed up the process.
    lftp_cmd = (
        f"lftp -u {username}, -e \"set sftp:connect-program 'ssh -o GSSAPIAuthentication=no "
        f"-o StrictHostKeyChecking=no -a -x -i {private_key_path}'; "
        f'mirror --parallel=10 {remote_data_path} {save_path}; quit" '
        f"sftp://{hostname}"
    )
    try:
        _LOG.info("Executing lftp command: %s", lftp_cmd)
        result = subprocess.run(
            lftp_cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        _LOG.error(
            "lftp command failed with error: %s",
            e.stderr,
        )


def get_sftp_connection(hostname: str, secret_name: str) -> pysftp.Connection:
    """
    Return SFTP connection object using a private key stored in AWS Secrets
    Manager.

    :param hostname: hostname of the SFTP server.
    :param secret_name: name of the secret in AWS Secrets Manager
        containing the private key.
    :return: active SFTP connection object.
    """
    # Fetch the private key from AWS Secrets Manager
    secret_dict = hsecret.get_secret(secret_name)
    username = secret_dict["username"]
    private_key = secret_dict["private_key"]
    # Write the private key to a temporary file
    with open("/tmp/temp_key.pem", "w") as temp_key_file:
        temp_key_file.write(private_key)
    # Ensure the key file has the correct permissions
    os.chmod("/tmp/temp_key.pem", 0o600)
    # Ensure pysftp is installed before attempting connection.
    cnopts = pysftp.CnOpts()
    # Disable host key checking.
    cnopts.hostkeys = None
    sftp = pysftp.Connection(
        hostname,
        username=username,
        private_key="/tmp/temp_key.pem",
        cnopts=cnopts,
    )
    # Remove the temporary key file after establishing the connection
    os.remove("/tmp/temp_key.pem")
    return sftp


def download_file_to_s3(
    sftp: pysftp.Connection,
    s3_client: haws.BaseClient,
    remote_dir: str,
    filename: str,
    s3_bucket: str,
    s3_prefix: str,
) -> None:
    """
    Download data from an SFTP server and upload it to an S3 bucket.

    :param sftp: An active SFTP Connection object.
    :param s3_client: An AWS Base client object to interact with S3.
    :param remote_dir: The directory on the SFTP server where the file
        is located.
    :param filename: The name of the file to download from the SFTP
        server.
    :param s3_bucket: The name of the S3 bucket to upload the file to.
    :param s3_prefix: The prefix (path) in the S3 bucket where the file
        will be stored.
    :return: None.
    """
    remote_path = f"{remote_dir}/{filename}"
    s3_key = f"{s3_prefix}/{filename}"
    with sftp.open(remote_path) as file_obj:
        # Download data from sftp server.
        file_data = file_obj.read()
        try:
            # Upload data to S3.
            s3_client.upload_fileobj(BytesIO(file_data), s3_bucket, s3_key)
            _LOG.info(
                "Uploaded: %s to s3://%s/%s", remote_path, s3_bucket, s3_key
            )
        except Exception as e:
            _LOG.error("Failed to upload file to S3. Error: %s", str(e))
            raise e


def get_file_names(sftp: pysftp.Connection, sftp_remote_dir: str) -> List[str]:
    """
    Retrieve all file names from a specified directory on a remote SFTP server.

    :param sftp: An active SFTP Connection object.
    :param sftp_remote_dir: The directory on the SFTP server from which
        to list file names.
    :return: A list of file names present in the specified directory on
        the SFTP server.
    """
    file_names = []
    for item in sftp.listdir_attr(sftp_remote_dir):
        file_names.append(item.filename)
    return file_names
