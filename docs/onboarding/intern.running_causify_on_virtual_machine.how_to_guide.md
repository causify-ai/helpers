# **Running Causify On Virtual Machine How-to-Guide**

<!-- toc -->

- [Step 1: Download VMware Workstation Pro](#step-1-download-vmware-workstation-pro)
- [Step 2: Set Up a New Virtual Machine](#step-2-set-up-a-new-virtual-machine)
- [Step 3: Install Ubuntu](#step-3-install-ubuntu)
- [Step 4: Check Internet Connection](#step-4-check-internet-connection)
  * [Recommended Method](#recommended-method)
  * [Alternative 1](#alternative-1)
  * [Alternative 2](#alternative-2)
- [Conclusion](#conclusion)

<!-- tocstop -->

## Step 1: Download VMware Workstation Pro

- There are a lot of errors while setting up the Oracle VirtualBox, so it is
  recommended to go ahead with VMWare Workstation Pro

- Go to the official
  [VMware Workstation and Fusion](https://www.vmware.com/products/desktop-hypervisor/workstation-and-fusion)
  page
- Click on `Download Fusion or Workstation`
- The user will be redirected to the Broadcom registration page.
  [Register](https://profile.broadcom.com/web/registration) and
  [Login](https://access.broadcom.com/default/ui/v1/signin/) yourself on the
  website
- Once logged in, go to the
  [Downloads Homepage](https://support.broadcom.com/group/ecx/downloads). Under
  `My Downloads`, click on `Free Software Downloads available HERE`
- Select `VMware Workstation Pro` and choose the latest release (or 17.6.3)
- Fill out few details and proceed to download
- Follow the installation prompts to set up VMware on the system

## Step 2: Set Up a New Virtual Machine

- Before proceeding, ensure that you have downloaded the latest version or
  **Ubuntu (24.04.2 LTS)** ISO file. It can be downloaded
  [here](https://ubuntu.com/download/desktop)

- Open VMware Workstation Pro and click on `New Virtual Machine`
- Choose the `Typical (Recommended)` configuration
- Under the `Installer disc image file (iso)` option, browse and select the path
  to your downloaded Ubuntu ISO file
- Set the disk size to **35GB** and select `Store virtual disk as a single file`
  - If you select `Split virtual disk into multiple files`, the 35GB will be
    split, so you might need to allocate more space for your section in the
    future but it works fine as well
- Completing the setup will take you directly to the Ubuntu installation screen

## Step 3: Install Ubuntu

- Choose `English` as your preferred language
- Select `Use wired connection`, even if you plan to use Wi-Fi
- Begin the installation and choose `Interactive Installation` option
- Proceed with the `Default Selection` during the installation
- Select both:
  - `Install third-party software for graphics and Wi-Fi hardware`
  - `Download and install support for additional media formats`
- Choose the `Erase disk and Install Ubuntu` option
- Set up your `name`, `password`, and `timezone` as per your preferences

- In case the installation fails or asks to report the issue, simply restart the
  virtual machine and repeat the process. It should work on the second try

## Step 4: Check Internet Connection

- Check your internet connection in the browser. If it works, you can skip this
  section!

### Recommended Method

- Shutdown the virtual machine
- In VMware Workstation, go to `Edit` in the top menu and select
  `Virtual Network Editor`
- Click `Change Settings` and ensure the following:
  - `VMnet0`: Bridged
  - `VMnet1`: Host-only
  - `VMnet8`: NAT
  - Both `VMnet1` and `VMnet8` should be connected and enabled
- For `VMnet0`, set the `Bridged to: Automatic` option and click on
  `Automatic Settings`. Uncheck all options except the one corresponding to your
  Wi-Fi address (you can find it in your host system's `Network Connections`)
  and apply the changes

### Alternative 1

- Instead of using `Automatic` for Bridged, manually select your Wi-Fi network
  from the dropdown list and apply the changes. Always restart the VM after any
  modifications

### Alternative 2

- Before starting the VM, go to `Network Adapter` under `Devices`, select
  `Bridged`, and check the option `Replicate physical network connection state`
- If it doesn't work, change to `NAT` and apply the settings. Restart the VM
  after each change

## Conclusion

- After completing these steps, you should have VMware Workstation Pro running
  Ubuntu with internet connectivity, ready to set up Docker
