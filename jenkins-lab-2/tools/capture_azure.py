"""Capture the Azure side of Lab 2 from the signed-in portal window.

Covers assignment requirement 1 ("Install VM in Microsoft Azure"): the resource
group, the VM itself, its size and region, and the network security group after
it was tightened to admit SSH from the controller only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import azure_portal as AZ

SUB = "86f4ee12-f7ba-469e-acb1-6b62403cf4e5"
RG = "rg-jenkins-lab2"
VM = "jenkins-agent-1"
NSG = "jenkins-agent-1-nsg"

RES = f"/subscriptions/{SUB}/resourceGroups/{RG}/providers"
VM_ID = f"{RES}/Microsoft.Compute/virtualMachines/{VM}"
NSG_ID = f"{RES}/Microsoft.Network/networkSecurityGroups/{NSG}"


def blade(path):
    return f"https://portal.azure.com/#@/resource{path}"


PAGES = [
    (AZ.PORTAL,
     "01-azure-portal-home.png",
     "Azure portal home, signed in as the lab account"),
    (f"https://portal.azure.com/#@/resource/subscriptions/{SUB}/resourceGroups/{RG}/overview",
     "03-azure-resource-group.png",
     "Resource group rg-jenkins-lab2 and everything the VM pulled in with it"),
    (blade(VM_ID + "/overview"),
     "04-azure-vm-overview.png",
     "The virtual machine: Running, with its public IP and region"),
    (blade(VM_ID + "/properties"),
     "05-azure-vm-properties.png",
     "VM properties - size, image and operating system"),
    (blade(VM_ID + "/networking"),
     "06-azure-vm-networking.png",
     "VM networking - the inbound rules attached to the NIC"),
    (blade(NSG_ID + "/overview"),
     "07-azure-nsg-rules.png",
     "The NSG after tightening: SSH from the controller's IP only"),
    ("https://portal.azure.com/#view/HubsExtension/BrowseAll",
     "08-azure-all-resources.png",
     "All resources created for the lab"),
]


def main():
    b = AZ.attach()
    print("portal session live", flush=True)
    try:
        for url, name, label in PAGES:
            try:
                AZ.capture(b, url, name, label, wait_ms=14000)
            except Exception as e:
                print(f"  !! {name} failed: {e}", flush=True)
    finally:
        b.close(keep_browser=True)


if __name__ == "__main__":
    main()
