

<!-- toc -->

- [VPN and dev server access setup](#vpn-and-dev-server-access-setup)
  * [VPN setup](#vpn-setup)
    + [Zip package with credentials](#zip-package-with-credentials)
    + [Install OpenVPN](#install-openvpn)
    + [Set up two-factor authentication](#set-up-two-factor-authentication)
    + [Set up the connection in your operating system](#set-up-the-connection-in-your-operating-system)
      - [Linux](#linux)
      - [Mac OS](#mac-os)
  * [Testing server login](#testing-server-login)
    + [Server login via SSH](#server-login-via-ssh)
  * [Troubleshooting common issues](#troubleshooting-common-issues)
    + [IPv6 causing DNS resolution failure](#ipv6-causing-dns-resolution-failure)

<!-- tocstop -->

# VPN and dev server access setup

- To log into the development system you need to use a VPN with two-factor
  authentication
- The VPN password is obtained by concatenating your fixed password and a
  6-digit token from the Google Authenticator app
- Once the VPN connection is established you can access the servers inside the
  virtual private network.

## VPN setup

### Zip package with credentials

You will receive an e-mail with a `.zip` file from the IT team containing all
the information you need to use the system. The ZIP file is encrypted and the
password is sent to your Slack direct messages.

We currently have two VPN servers, one US-based and one EU-based.

Choose one location based on your physical proximity.

Both directories `<username>@vpn1.<region>\_embedded` contain files to set up
the VPN access:

- `<< username >>@vpn1.<<aws_region>>_embeded/`
- `<< username >>@vpn1.<< aws_region >>-pki-embedded.ovpn`
  - This file can be imported directly into your VPN client or a command-line
    tool
- `<< username >>@vpn1.<< aws_regoion >>-totp.seed`
  - Contains instructions on how to set-up two-factor authentication

The `user_credentials` directory contains all of your user credentials and login
information

- `vpn_password.txt`: your VPN password
- `pem_passphrase.txt`: password to the private key of your user certificate
- `server_ip.txt`: IP addresses of our dev servers
- `crypto.pub`: public key you have provided (just to verify that the account
  creation was done using the correct key pair)

### Install OpenVPN

You need to install client version 3 on your laptop following
[https://openvpn.net/vpn-client](https://openvpn.net/vpn-client)

### Set up two-factor authentication

Install an authenticator app on your phone from AppStore or Google Play (e.g.,
[<span class="underline">Google Authenticator</span>](https://en.wikipedia.org/wiki/Google_Authenticator))

Use the `\*-totp.seed` file to initialize the authenticator

```verbatim
["Warning: pasting the following URL into your browser exposes the OTP
secret to Google:", "
https://www.google.com/chart?chs=200x200&chld=M|0&cht=qr&chl=otpauth://totp/saggese@vpn1.eu-north-1%3Fsecret***",
"Your new secret key is: ****", "Your verification code is ***",
"Your emergency scratch codes are:", " ***", " ***", " ***", "
***", " ***"]
```

You can either visit the URL in the file which shows you a QR code to scan with
your authenticator app or create the entry by pasting the secret key yourself.

Once imported you are going to get a six-digit code (like 014356) from the
authenticator that expires every minute

### Set up the connection in your operating system

#### Linux

- You can use the command line tool to connect
  - Quick tutorial is available
    [here](https://openvpn.net/vpn-server-resources/connecting-to-access-server-with-linux)

- Command example;

  ```bash
  > sudo cat auth.cfg | openvpn3 session-start --config your_ovpn.ovpn
  ```
  - Be sure to put your credentials in auth.cfg (name of the file does not
    matter) in the right order (each credential on a separate line):
    - Username
    - Password + two-factor auth generated code
    - Passphrase
  - To have at least some kind of security make your file accessible only by the
    root user with the commands below:
    ```bash
    > chown root:root /path/to/your/file
    > chmod 600 /path/to/your/file
    ```

- Note: Use the GUI approach below only as a last resort!
  - It uses openvpn2 under the hood and it will give you a headache

- Alternatively, if you are a Ubuntu user you can use the built-in VPN manager
  in Settings -> Network -> VPN -> Add VPN -> Import from file… where you choose
  the embedded `.ovpn` file (see screenshot below)

  <img src="figs/setup_vpn_and_dev_server_access/image1.png">

- If you decide to take the GUI approach above, do not forget to check
  `Use this connection only for resources on its network` as seen in the
  screenshot below

  <img src="figs/setup_vpn_and_dev_server_access/image3.png">

#### Mac OS

- Follow the instructions at
  [https://openvpn.net/client-connect-vpn-for-mac-os/](https://openvpn.net/client-connect-vpn-for-mac-os/)

- Import the profile via GUI, see the screenshot below
  <img src="figs/setup_vpn_and_dev_server_access/image2.png">

- Import the profile, e.g.,
  `<saggese@vpn1.eu>-north-1_embeded/<saggese@vpn1.eu>-north-1-pki-embedded.ovpn`
  or `saggese@vpn1.us-east-1_embedded/saggese@vpn1.us-east-1-pki-embedded.ovpn`

You can log in to the VPN by inputting:

- For password, the VPN password from `user_credentials/vpn_password.txt`,
  concatenated with 6 digit code from the authenticator app e.g. your
  vpn_password.txt is `D28DND73T71NF0` and your active PIN from Authenticator is
  `556665`, you need to enter `D28DND73T71NF0556665`

- For private key password the content of
  `user_credentials/vpn_pem_passphrase.txt`

- You can enable the `Save Private Key Password` since this doesn't change,
  while you can't save the password since that is changing every time.

  <img src="figs/setup_vpn_and_dev_server_access/image6.png">

- E.g., to login

  ```bash
  # Get the VPN password
  > more ~/Desktop/saggese/user_credentials/vpn_password.txt
  # Open the Authenticator
  > ...
  Concat the password and enter
  ```

  <img src="figs/setup_vpn_and_dev_server_access/image5.png">

- After you log in you should see:

  <img src="figs/setup_vpn_and_dev_server_access/image4.png">

## Testing server login

After you have an OpenVPN connection running you can log into one of the dev
servers.

There are 2 dev servers to spread the load on the servers and to have a
secondary server if something happens to one of them.

The IP of the servers:

```verbatim
dev1: 172.30.2.136
dev2: 172.30.2.128
```

Confirming with your team leader, which server should be the main one for you.

### Server login via SSH

Test that your VPN connection is working by logging into the server.

- The IP of the servers:

  ```verbatim
  dev1: 172.30.2.136
  dev2: 172.30.2.128
  ```

- To ssh in the server, use the private key that you have generated in the
  beginning
  ```bash
  > ssh -i ... ${USER}@172.30.2.136
  ```
- E.g.,
  ```bash
  > ssh -i ~/.ssh/cryptomatic/saggese-cryptomatic.pem saggese@172.30.2.136
  ```

## Troubleshooting common issues

### IPv6 causing DNS resolution failure

- This issue prevents user from accessing internal systems such as Airflow UI
  due to DNS resolution failures
  - Error output from terminal:
    ```bash
    > curl http://internal-a97b7f81b909649218c285140e74f68a-1285736094.eu-north-1.elb.amazonaws.com:8080/home
    curl: (6) Could not resolve host: internal-a97b7f81b909649218c285140e74f68a-1285736094.eu-north-1.elb.amazonaws.com
    ```
  - Error output from web browser:
    ```verbatim
    This site can't be reached
    ```
- It occurs when the user's system is configured to use IPv6 but the network
  infrastructure is not set up to handle IPv6 properly
- In other words, the DNS settings aren't configured to handle IPv6 addresses
  (AAAA records)
- Hence, the IPv6 system fails to resolve and reach the server

Resolution: Force the use of IPv4

1. Update DNS settings

- Change local DNS resolver to Google’s public DNS servers (`8.8.8.8`)
- On MacOS, go to `Setting` > `Wi-Fi` > select `Details` on current Wi-Fi
  connection > `DNS` > add `8.8.8.8` addresses to `DNS Servers` configuration
  - <img src="figs/troubleshooting/ipv6_dns_resolution_failure.png"
    style="width:6in" />

2. Flush the DNS cache

- Clear cached DNS records to ensure the new settings take effect
  - On MacOS, execute
    ```bash
    sudo killall -HUP mDNSResponder
    ```

3. Disconnect and reconnect to Wi-Fi

4. Reconnect to VPN
