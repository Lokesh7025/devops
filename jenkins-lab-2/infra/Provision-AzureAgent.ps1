<#
.SYNOPSIS
    Provisions the Azure Linux VM that Jenkins Lab 2 uses as a build agent.

.DESCRIPTION
    Creates a resource group, an Ubuntu 24.04 VM with SSH-key authentication,
    and an NSG rule that admits SSH from this machine's public IP only.

    Why SSH rather than an inbound (JNLP) agent: the Jenkins controller runs on
    a laptop behind NAT, so the VM cannot dial in to it. Reversing the direction
    -- controller connects out to the VM on port 22 -- is what makes the lab
    work without exposing the controller to the internet.

    The build toolchain (JDK 21, Maven, git) is installed by cloud-init.yaml
    at first boot rather than by a later SSH session, so the VM is reproducible
    from this script alone.

.NOTES
    Nothing here reads or stores a password. The key pair is generated locally
    and only the public half is ever sent to Azure.
#>
param(
    [string]$ResourceGroup = 'rg-jenkins-lab2',
    [string]$VmName        = 'jenkins-agent-1',
    [string]$AdminUser     = 'azureuser',

    # Azure hands out compute per-region, and a brand-new subscription is the
    # first thing turned away when a region is tight. Central India refused
    # Standard_B2s outright ("SkuNotAvailable ... Capacity Restrictions"), so
    # the script walks a candidate list instead of hard-coding one region:
    # nearest first, then progressively further afield.
    [string[]]$Candidates = @(
        'centralindia:Standard_B2s',
        'centralindia:Standard_D2s_v3',
        'southindia:Standard_B2s',
        'southeastasia:Standard_B2s',
        'southeastasia:Standard_D2s_v3',
        'eastus:Standard_B2s'
    )
)

$ErrorActionPreference = 'Stop'
$root    = 'C:\Users\lokes\jenkins-lab\lab2'
$keyDir  = Join-Path $root 'ssh'
$keyFile = Join-Path $keyDir 'jenkins_agent_key'
$cloudInit = Join-Path $PSScriptRoot 'cloud-init.yaml'

New-Item -ItemType Directory -Force -Path $keyDir | Out-Null

# --- 1. key pair -----------------------------------------------------------
# RSA-4096 rather than ed25519: it is accepted by every Jenkins SSH agent
# implementation, including the older trilead-based ones.
if (-not (Test-Path "$keyFile")) {
    Write-Host '[1/6] generating SSH key pair' -ForegroundColor Cyan
    ssh-keygen -t rsa -b 4096 -f $keyFile -N '""' -C 'jenkins-lab2-agent' | Out-Null
} else {
    Write-Host '[1/6] reusing existing SSH key pair' -ForegroundColor Cyan
}

# --- 2. my public IP -------------------------------------------------------
$myIp = (Invoke-RestMethod -Uri 'https://api.ipify.org?format=json' -TimeoutSec 20).ip
Write-Host "[2/6] restricting SSH to $myIp" -ForegroundColor Cyan

# --- 3. resource group -----------------------------------------------------
$Location = ($Candidates[0] -split ':')[0]
$rgLocation = az group show --name $ResourceGroup --query location -o tsv
if ($LASTEXITCODE -eq 0 -and $rgLocation) {
    # A resource group's location is only where its metadata lives; resources
    # inside it may sit in any region. So an existing group is reused as-is
    # rather than recreated - az group create rejects a location change.
    Write-Host "[3/6] reusing resource group $ResourceGroup ($rgLocation)" -ForegroundColor Cyan
} else {
    Write-Host "[3/6] resource group $ResourceGroup in $Location" -ForegroundColor Cyan
    az group create --name $ResourceGroup --location $Location --output none
    if ($LASTEXITCODE -ne 0) { throw "could not create the resource group" }
}

# --- 4. the VM -------------------------------------------------------------
# --nsg-rule NONE suppresses the default "SSH open to the internet" rule; the
# tightened rule is added in step 5 instead.
$VmSize = $null
foreach ($candidate in $Candidates) {
    $loc, $size = $candidate -split ':'
    Write-Host "[4/6] trying $size in $loc" -ForegroundColor Cyan
    az vm create `
        --resource-group $ResourceGroup `
        --name $VmName `
        --location $loc `
        --image Ubuntu2404 `
        --size $size `
        --admin-username $AdminUser `
        --ssh-key-values "$keyFile.pub" `
        --public-ip-sku Standard `
        --nsg-rule NONE `
        --custom-data $cloudInit `
        --output none
    if ($LASTEXITCODE -eq 0) {
        $Location = $loc
        $VmSize   = $size
        Write-Host "      created in $loc as $size" -ForegroundColor Green
        break
    }
    Write-Host "      unavailable, trying the next candidate" -ForegroundColor Yellow
    # A failed create still leaves the networking behind, and those resources
    # are pinned to the region that just refused us - so they have to go before
    # the next region is attempted. Delete in dependency order: the NIC holds
    # references to the IP, NSG and subnet.
    foreach ($type in @('networkInterfaces', 'publicIPAddresses',
                        'networkSecurityGroups', 'virtualNetworks')) {
        az resource list --resource-group $ResourceGroup `
            --query "[?type=='Microsoft.Network/$type'].id" -o tsv |
            ForEach-Object { if ($_) { az resource delete --ids $_ --output none } }
    }
}
if (-not $VmSize) { throw "no candidate region/size combination had capacity" }

# --- 5. lock the NSG down --------------------------------------------------
Write-Host '[5/6] adding the SSH rule' -ForegroundColor Cyan
az network nsg rule create `
    --resource-group $ResourceGroup `
    --nsg-name "${VmName}NSG" `
    --name allow-ssh-from-controller `
    --priority 300 `
    --access Allow --protocol Tcp --direction Inbound `
    --source-address-prefixes "$myIp" `
    --source-port-ranges '*' `
    --destination-address-prefixes '*' `
    --destination-port-ranges 22 `
    --description 'SSH from the Jenkins controller only' `
    --output none
if ($LASTEXITCODE -ne 0) { throw "could not add the SSH rule" }

# --- 6. report -------------------------------------------------------------
$publicIp = az vm show -d --resource-group $ResourceGroup --name $VmName --query publicIps -o tsv
if ($LASTEXITCODE -ne 0 -or -not $publicIp) { throw "the VM has no public IP" }
Write-Host '[6/6] done' -ForegroundColor Green
Write-Host ''
Write-Host "  VM         : $VmName ($VmSize, $Location)"
Write-Host "  Public IP  : $publicIp"
Write-Host "  User       : $AdminUser"
Write-Host "  Private key: $keyFile"
Write-Host ''
Write-Host "  ssh -i `"$keyFile`" $AdminUser@$publicIp"

@{ resourceGroup = $ResourceGroup; location = $Location; vmName = $VmName
   vmSize = $VmSize; adminUser = $AdminUser; publicIp = $publicIp
   keyFile = $keyFile; allowedFrom = $myIp } |
    ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $root 'vm.json')
