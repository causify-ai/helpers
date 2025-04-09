<!-- toc -->

- [**Running Cauify On Windows How-to-Guide**](#running-cauify-on-windows-how-to-guide)
  * [**Index**](#index)
  * [**Step 1: Download VMware Workstation Pro**](#step-1-download-vmware-workstation-pro)
  * [**Step 2: Set Up a New Virtual Machine**](#step-2-set-up-a-new-virtual-machine)
  * [**Step 3: Install Ubuntu**](#step-3-install-ubuntu)
  * [**Step 4: Check Internet Connection**](#step-4-check-internet-connection)
      - [Recommended Method](#recommended-method)
  * [**Conclusion**](#conclusion)

<!-- tocstop -->

# **Running Cauify On Windows How-to-Guide**

## **Index**

1. [Download VMware Workstation Pro](#step-1-download-vmware-workstation-pro)
2. [Set Up a New Virtual Machine](#step-2-set-up-a-new-virtual-machine)
3. [Install Ubuntu](#step-3-install-ubuntu)
4. [Check Internet Connection](#step-4-check-connection)
5. [Conclusion](#step-5-conclusion)

## **Step 1: Download VMware Workstation Pro**

There are a lot of errors while setting up the Oracle VirtualBox, so it is
recommended to go ahead with VMWare Workstation Pro.

1. **Visit the VMware Website:**
   Go to the official VMware page:
   [VMware Workstation and Fusion](https://www.vmware.com/products/desktop-hypervisor/workstation-and-fusion).
   Click
   on **Download Fusion or Workstation**.

2. **Register and Log In:**
   You'll be redirected to the Broadcom registration page.
   At the top-right corner, click on **Login** and then **Register**.

3. **Complete User Registration:**
   Fill in the required details and log in to the Broadcom page.

4. **Navigate to Downloads:**
   Once logged in, go to their
   [Downloads Homepage](https://support.broadcom.com/group/ecx/downloads).
   Under **My Downloads**, click on **Free Software Downloads**.

5. **Download VMware Workstation Pro:**
   Select **VMware Workstation Pro** and choose the latest release (or 17.6.3).

6. **Provide Additional Details:**
   After selecting the version, you'll be asked to complete a few details. Fill
   them out and proceed to download.

7. **Install VMware Workstation Pro:**
   Follow the installation prompts to set up VMware on your system.

## **Step 2: Set Up a New Virtual Machine**

Before proceeding, ensure that you have downloaded the **Ubuntu (24.04.2 LTS or
the latest version)** ISO file. You can download it
[here](https://ubuntu.com/download/desktop).

1. **Open VMware Workstation Pro:**
   Launch VMware Workstation and click on **New Virtual Machine**.

2. **Select Installation Type:**
   Choose the **Typical (Recommended)** configuration.

3. **Choose ISO File:**
   Under the **Installer disc image file (iso)** option, browse and select the
   path to your downloaded Ubuntu ISO file.

4. **Set Virtual Disk Size:**
   Set the disk size to **35GB** and select the option to **Store virtual disk
   as a single file**.
   (Note: If you select "Split virtual disk into multiple files", the 35GB will
   be split, so you might need to allocate more space for your section in future
   but it works fine as well.)

5. **Finalize Virtual Machine Setup:**
   Complete the setup, and VMware will take you directly to the Ubuntu
   installation screen.

## **Step 3: Install Ubuntu**

1. **Select Language:**
   Choose **English** as your preferred language.

2. **Network Connection:**
   Select **Use wired connection**, even if you plan to use Wi-Fi.

3. **Install Ubuntu:**
   Click on the **Install Ubuntu** button to begin the installation.

4. **Choose Installation Type:**
   For Cauify, go with the **Interactive Installation** option.

5. **Default Selection:**
   Proceed with the **Default Selection** during the installation.

6. **Install Additional Software:**
   Select both:
   - **Install third-party software for graphics and Wi-Fi hardware**
   - **Download and install support for additional media formats**

7. **Erase Disk and Install Ubuntu:**
   Choose the **Erase disk and Install Ubuntu** option.

8. **Create User Account:**
   Set up your **name**, **password**, and **timezone** as per your preferences.

In case the installation fails or asks to report the issue, simply restart the
virtual machine and repeat the process. It should work on the second try.

## **Step 4: Check Internet Connection**

Go to the firefox and check internet connection. If it works, you can skip this
section.

### Recommended Method

1. **Shutdown Virtual Machine:**
   Power off the virtual machine.

2. **Access Network Settings:**
   In VMware Workstation, go to **Edit** in the top menu and select **Virtual
   Network Editor**.

3. **Change Network Settings:**
   Click **Change Settings** and ensure the following:
   - **VMnet0**: Bridged
   - **VMnet1**: Host-only
   - **VMnet8**: NAT
   - Both **VMnet1** and **VMnet8** should be connected and enabled.

4. **Configure Bridged Network:**
   For **VMnet0**, set the **Bridged to: Automatic** option and click on
   **Automatic Settings**. Uncheck all options except the one corresponding to
   your Wi-Fi address (you can find it in your host system's **Network
   Connections**) and Apply the changes.

**Alternative 1:**
Instead of using **Automatic** for Bridged, manually select your Wi-Fi network
from the dropdown list and apply the changes. Always **restart** the VM after
any modifications.

**Alternative 2:**
Before starting the VM, go to **Network Adapter** under **Devices**, select
**Bridged**, and check the option **Replicate physical network connection
state**.
If it doesn't work, change to **NAT** and apply the settings.
**Restart** the VM after each change.

## **Conclusion**

After completing these steps, you should have VMware Workstation Pro running
Ubuntu with internet connectivity, ready to set up Docker.
