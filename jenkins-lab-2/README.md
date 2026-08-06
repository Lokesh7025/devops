# Jenkins Lab 2

**Build a project using one agent node.**

| | |
|---|---|
| Student | Lokesh Selvam |
| Repository | `Lokesh7025/devops`, branch `jenkins-lab-2` |
| Controller | Jenkins 2.568.1 LTS, Windows 11, `http://localhost:8080` |
| Agent | `azure-agent-1` — Ubuntu 24.04.4 LTS VM in Microsoft Azure |
| Project built | `com.snake:snake-game` (Maven, produces `snake.jar`) |

The assignment had three parts. All three are done, and the evidence for each is
a screenshot plus a build log rather than an assertion:

| # | Requirement | Where to look |
|---|---|---|
| 1 | Install VM in Microsoft Azure | screenshots 03–08 |
| 2 | Connect the VM as agent node | screenshots 10–16 |
| 3 | Configure Jenkins to run the stage in the VM and build the project | screenshots 17–22, and `logs/` |

---

## 1. The architecture, and why it is shaped this way

The controller runs on a laptop behind NAT on a campus network. The agent is a
VM with a public IP in Azure. That single fact decides the whole design.

Jenkins can connect an agent in two directions:

- **Inbound (JNLP)** — the agent dials the controller. This needs the controller
  to be reachable from the internet. It is not, and exposing it would be a bad
  idea even if it were.
- **Outbound (SSH)** — the controller dials the agent on port 22. This works
  through NAT without exposing anything, because the connection is initiated
  from inside.

So the lab uses the **SSH launcher**. The controller opens an SSH session to the
VM, copies `remoting.jar` across, starts a JVM there, and speaks the Jenkins
remoting protocol over that pipe. Nothing on the controller listens publicly;
the only inbound port anywhere is 22 on the VM, and that is restricted to a
single source address.

```
  Windows 11 laptop (NAT)                        Microsoft Azure, Central India
 ┌──────────────────────────┐                   ┌──────────────────────────────┐
 │ Jenkins controller       │   SSH :22         │ jenkins-agent-1              │
 │ localhost:8080           │ ─────────────────>│ Ubuntu 24.04, D2ls v5        │
 │                          │   remoting.jar    │ 20.244.18.166                │
 │ built-in node (Windows)  │ <─ ─ ─ ─ ─ ─ ─ ─ ─│ JDK 21 · Maven 3.8.7 · git   │
 └──────────────────────────┘   remoting proto  └──────────────────────────────┘
                                                            │ SSH deploy key
                                                            v
                                                   github.com/Lokesh7025/devops
```

Note the second arrow at the bottom: the **agent** clones the repository, not
the controller. That is what makes the build genuinely remote.

---

## 2. Step 1 — the virtual machine in Azure

| Property | Value |
|---|---|
| Name | `jenkins-agent-1` |
| Resource group | `rg-jenkins-lab2` |
| Region | Central India (Zone 1) |
| Size | `Standard_D2ls_v5` — 2 vCPU, 4 GiB |
| Image | Ubuntu Server 24.04 LTS, x64 Gen2 |
| Public IP | `20.244.18.166` |
| Admin user | `azureuser`, SSH public-key authentication only |
| Disk | 29 GiB, 26 GiB free |
| Kernel | `Linux 6.17.0-1021-azure x86_64` |

### The free-trial obstacle

The intention was to create this with the Azure CLI, and
[`infra/Provision-AzureAgent.ps1`](infra/Provision-AzureAgent.ps1) is that
script. It never succeeded. Every size in every region was refused:

```
(SkuNotAvailable) The requested VM size for resource 'Following SKUs have failed
for Capacity Restrictions: Standard_B2s' is currently not available in location
'CentralIndia'. Please try another size or deploy to a different location...
```

Ten combinations were tried before concluding the message was misleading:

| Region | Sizes attempted | Result |
|---|---|---|
| Central India | B2s, D2s_v3, B1s, DS1_v2 | all refused |
| South India | B2s | refused |
| Southeast Asia | B2s, D2s_v3, B1s | all refused |
| East US | B2s, B1s, B1ms, DS1_v2, A2_v2, D2as_v5, B2als_v2 | all refused |
| West US 2 | B1s | refused |

It was not a quota problem — `az vm list-usage` showed **0 of 4** regional vCPUs
in use. Querying the subscription directly explained it:

```
az rest --url "https://management.azure.com/subscriptions/<id>?api-version=2022-12-01"
{ "quotaId": "FreeTrial_2014-09-01", "spendingLimit": "On", "state": "Enabled" }
```

A **free-trial subscription is restricted from most VM SKUs**, and Azure
surfaces that restriction as "Capacity Restrictions" — wording that points at
the datacentre rather than at the account. The Azure portal says it plainly in
the create-VM blade: *"This subscription may not be eligible to deploy VMs of
certain sizes in certain regions."*

The VM was therefore created through the **portal**, whose size picker only
offers SKUs the subscription can actually deploy. `Standard_D2ls_v5` was
permitted, in Central India — the same region the CLI had refused minutes
earlier for four other sizes.

> **Lesson worth recording:** on a restricted subscription, the portal's size
> list is authoritative and the CLI's error message is not. `SkuNotAvailable`
> can mean "your subscription may not buy this", not "the region is full".

The provisioning script is kept in the submission anyway: it is the correct,
reproducible path on any normal subscription, and it carries the cloud-init
file and the NSG hardening logic.

### Hardening the network

The portal's defaults opened **three** ports to the entire internet:

| Rule | Priority | Source | Port |
|---|---|---|---|
| HTTP | 300 | `*` | 80 |
| HTTPS | 320 | `*` | 443 |
| SSH | 340 | `*` | 22 |

80 and 443 serve nothing on this VM, and SSH open to the world on a box holding
a build agent is an unnecessary invitation. After tightening:

| Rule | Priority | Source | Port |
|---|---|---|---|
| SSH | 340 | `14.139.161.250` | 22 |

That single source is the controller's public address. Screenshot 07 shows the
result.

### Toolchain

Installed over SSH after first boot:

```
openjdk version "21.0.11"     /usr/lib/jvm/java-21-openjdk-amd64
Apache Maven 3.8.7
git version 2.43.0
```

---

## 3. Step 2 — connecting the VM as an agent node

Three pieces had to line up.

**The plugin.** `ssh-slaves` (SSH Build Agents) provides the SSH launch method.
It was already present from the recommended set installed in Lab 1.

**The credential.** The agent authenticates with an RSA-4096 key pair generated
locally; only the public half was ever given to Azure. The private half is
registered as a Jenkins credential, `azure-agent-ssh`. It was added through the
script console so that Jenkins reads the key off disk itself — a private key
should not be typed into a browser form by automation.

**The node.**

| Setting | Value |
|---|---|
| Name | `azure-agent-1` |
| Remote root directory | `/home/azureuser/jenkins` |
| Labels | `azure linux` |
| Executors | 1 |
| Usage | Use this node as much as possible |
| Launch method | Launch agents via SSH |
| Host | `20.244.18.166`, port 22 |
| Credentials | `azure-agent-ssh` |
| Host key strategy | Non-verifying (see *Security notes*) |
| Availability | Keep this agent online as much as possible |

The agent came online **10 seconds** after the node was created. Screenshot 12
is the connection log; `remoting.jar` and a `remoting/` directory appear under
`/home/azureuser/jenkins`, which is the controller having pushed its remoting
layer across.

---

## 4. Step 3 — running the stage on the VM

The pipeline is [`Jenkinsfile`](../Jenkinsfile), read from this branch by a
Pipeline job called `snake-game-on-azure-agent`. Defining the stages in the
repository rather than in the Jenkins UI matters: it means

```groovy
pipeline {
    agent { label 'azure' }
```

is authoritative. The build cannot quietly fall back to the controller, because
there is no controller-side script to fall back to.

| Stage | What it does |
|---|---|
| Where am I running | prints `NODE_NAME`, hostname, kernel, distro, public IP |
| Toolchain | `java -version`, `mvn -version`, `git --version` |
| Checkout | `checkout scm`, then the resolved commit |
| Build | `mvn -B -ntp clean package` |
| Verify artifact | lists `target/snake.jar`, prints its manifest and SHA-256 |
| Archive | `archiveArtifacts` with fingerprinting |

The first stage exists purely as evidence. Rather than asking a reader to trust
the node configuration page, the build log itself states which machine it ran
on.

### Repository access from the agent

The repository is private, and this is where Lab 1's arrangement stopped
working. In Lab 1 the checkout ran on the Windows controller, where Git
Credential Manager supplied credentials invisibly. The Azure agent has no such
helper and no stored credentials, so the clone has to carry its own key.

A **read-only SSH deploy key** was generated for this and added to the
repository. A deploy key is the narrowest option available: it is scoped to one
repository, cannot write, and is not tied to the account's other repositories —
unlike a personal access token, which would have to be scoped down deliberately.

The job therefore checks out over SSH:

```
git@github.com:Lokesh7025/devops.git   branch */jenkins-lab-2
credential: github-deploy-key
```

GitHub's host keys were seeded into `~/.ssh/known_hosts` on both the controller
and the agent, so the default "known hosts file" verification strategy is
satisfied without weakening it.

### The result

Build **#2** — `SUCCESS`. Full log: [`logs/build-2-console.txt`](logs/build-2-console.txt).

The lines that answer the assignment:

```
Running on azure-agent-1 in /home/azureuser/jenkins/workspace/snake-game-on-azure-agent

Jenkins node : azure-agent-1
Host         : jenkins-agent-1
User         : azureuser
Kernel       : Linux 6.17.0-1021-azure x86_64
Distro       : Ubuntu 24.04.4 LTS
Public IP    : 20.244.18.166
```

The controller is Windows 11. The build reports a `6.x-azure` kernel, Ubuntu
24.04, and the VM's own public IP. It cannot have run anywhere but the agent.

The rest of it:

```
Checking out Revision ab2ddb8bf7d3c238e396d2741ce1afccd0a5d100 (refs/remotes/origin/jenkins-lab-2)
[INFO] Building jar: .../target/snake.jar
[INFO] BUILD SUCCESS
[INFO] Total time:  13.275 s
-rw-rw-r-- 1 azureuser azureuser 573K Aug  6 06:51 target/snake.jar
c7846fe0e9a766f5039a2ba9d063dd82a3497e4877b6ac04f04444a17dbf6ea0  target/snake.jar
Archiving artifacts
```

Cross-checks that the evidence is internally consistent:

| Claim | Corroboration |
|---|---|
| It built this branch | `ab2ddb8` is the head of `jenkins-lab-2`, the commit that added the Jenkinsfile |
| It built on Linux | file mode `-rw-rw-r--`, owner `azureuser`, path under `/home/azureuser` |
| The artifact is real | 573 KB shaded jar, SHA-256 recorded above, archived and fingerprinted |
| Maven ran remotely | 13.3 s build on a 2-vCPU VM, dependencies resolved into the agent's own `~/.m2` |

---

## 5. Two failures worth documenting

### `Cannot run program "git.exe"`

The first build allocated the agent, created the workspace at
`/home/azureuser/jenkins/workspace/snake-game-on-azure-agent`, and then died:

```
Caused by: java.io.IOException: Cannot run program "git.exe"
  (in directory "/home/azureuser/jenkins/workspace/snake-game-on-azure-agent"):
  Exec failed, error: 2 (No such file or directory)
ERROR: Error cloning remote repo 'origin'
```

Jenkins' **global** Git tool had been configured as `git.exe` in Lab 1 — correct
for a Windows controller, meaningless on Ubuntu. Tool configuration is global by
default, so the agent inherited a Windows path.

The fix is not to change the global setting, which would break the Windows side.
It is a **node-level tool location**, which is precisely what that Jenkins
feature is for: same tool, different path per machine.

| Scope | Git path |
|---|---|
| Global (`Default`) | `git.exe` |
| Node override on `azure-agent-1` | `/usr/bin/git` |

This is the single most transferable thing in the lab: **a heterogeneous
controller/agent pair cannot share absolute tool paths.**

### The free-trial SKU restriction

Covered in section 2. Summarised here because it cost the most time: a
misleading error message sent the investigation towards regional capacity when
the cause was the subscription's offer type.

---

## 6. Security notes

Written plainly rather than glossed, because the shortcuts matter more than the
things done correctly.

- **SSH is restricted to one source address.** If the controller's public IP
  changes — likely on a campus network — the rule needs updating before the
  agent will reconnect.
- **The agent's host key is not verified.** The node uses the non-verifying
  strategy, so the first connection would accept any host key. On a VM created
  minutes earlier and reachable only from one address the exposure is small, but
  a production setup should pin the key from the Azure boot diagnostics.
- **The deploy key is read-only and repository-scoped.** It cannot push, and it
  grants nothing on the rest of the account.
- **Private keys are not in this repository.** They live outside it, at
  `C:\Users\lokes\jenkins-lab\lab2\ssh\`. Only public halves and fingerprints
  appear in the report.
- **The Jenkins admin password was reset during the lab** because it was not
  recoverable — Jenkins stores a bcrypt hash by design. The documented recovery
  was used: stop the controller, set `<useSecurity>false</useSecurity>`, restart,
  set a new password through the script console, restore the original config,
  restart. The unsecured window lasted seconds and Jenkins listens on localhost
  only.

---

## 7. Cost

`Standard_D2ls_v5` is roughly ₹4–5 per hour. The lab consumed well under an
hour of runtime, comfortably inside the free-trial credit. The VM should be
deallocated when it is no longer needed:

```
az vm deallocate --resource-group rg-jenkins-lab2 --name jenkins-agent-1
```

Deallocating stops compute charges; the disk continues to cost a trivial amount.
To remove everything:

```
az group delete --name rg-jenkins-lab2 --yes
```

---

## 8. Screenshot index

Every screenshot is a real capture of the running system, saved to file — not a
crop of a browser window. They are numbered in the order the lab performed them.

### Requirement 1 — the VM in Azure

| # | File | What it shows |
|---|---|---|
| 01 | [`01-azure-portal-home.png`](screenshots/01-azure-portal-home.png) | Azure portal, signed in as the lab account |
| 02 | [`02-azure-subscription.png`](screenshots/02-azure-subscription.png) | The subscription the lab billed against |
| 03 | [`03-azure-resource-group.png`](screenshots/03-azure-resource-group.png) | `rg-jenkins-lab2` and everything the VM pulled in with it |
| 04 | [`04-azure-vm-overview.png`](screenshots/04-azure-vm-overview.png) | **The VM: Running, Ubuntu 24.04, D2ls v5, Central India, 20.244.18.166** |
| 05 | [`05-azure-vm-properties.png`](screenshots/05-azure-vm-properties.png) | VM properties — size, image, operating system |
| 06 | [`06-azure-vm-networking.png`](screenshots/06-azure-vm-networking.png) | The inbound rules attached to the NIC |
| 07 | [`07-azure-nsg-rules.png`](screenshots/07-azure-nsg-rules.png) | **The NSG after hardening: SSH from the controller's IP only** |
| 08 | [`08-azure-all-resources.png`](screenshots/08-azure-all-resources.png) | Every resource created for the lab |

### Requirement 2 — the agent node

| # | File | What it shows |
|---|---|---|
| 09 | [`09-jenkins-dashboard.png`](screenshots/09-jenkins-dashboard.png) | The Jenkins dashboard, signed in |
| 10 | [`10-jenkins-ssh-plugin.png`](screenshots/10-jenkins-ssh-plugin.png) | The SSH Build Agents plugin that provides the launcher |
| 11 | [`11-jenkins-credential.png`](screenshots/11-jenkins-credential.png) | Both credentials — the agent SSH key and the repo deploy key |
| 12 | [`12-agent-connection-log.png`](screenshots/12-agent-connection-log.png) | **The connection log — Jenkins pushing remoting over SSH** |
| 13 | [`13-jenkins-nodes.png`](screenshots/13-jenkins-nodes.png) | **The Nodes page: Windows built-in node plus the Linux Azure agent** |
| 14 | [`14-agent-overview.png`](screenshots/14-agent-overview.png) | The agent node — labels, executor, remote root |
| 15 | [`15-agent-configure.png`](screenshots/15-agent-configure.png) | Node configuration — SSH launcher and the Linux git tool location |
| 16 | [`16-agent-system-info.png`](screenshots/16-agent-system-info.png) | System info reported by the agent — a Linux JVM in Azure |

### Requirement 3 — the build

| # | File | What it shows |
|---|---|---|
| 17 | [`17-pipeline-job-config.png`](screenshots/17-pipeline-job-config.png) | The pipeline job, reading its definition from the repository |
| 18 | [`18-build-in-progress.png`](screenshots/18-build-in-progress.png) | **A build genuinely in flight on the agent** |
| 19 | [`19-build-console-top.png`](screenshots/19-build-console-top.png) | **Console log — `Running on azure-agent-1`, and the Ubuntu kernel** |
| 20 | [`20-build-result.png`](screenshots/20-build-result.png) | The successful build with `snake.jar` archived |
| 21 | [`21-pipeline-stage-view.png`](screenshots/21-pipeline-stage-view.png) | **Stage view — all six stages, all on the agent** |
| 22 | [`22-agent-build-history.png`](screenshots/22-agent-build-history.png) | Build history recorded against the agent node |

---

## 9. Repository layout

```
jenkins-lab-2/
├── README.md          this report
├── screenshots/       every screenshot, numbered in execution order
├── infra/             the provisioning script, cloud-init, and vm.json
├── jobs/              exported config.xml for the job and the node
├── logs/              full console logs
└── tools/             the scripts that drove and captured the lab
```

The Maven project and the [`Jenkinsfile`](../Jenkinsfile) live at the repository
root, one level up, because that is where the pipeline expects them.

---

## 10. Reproducing this

1. `az login`
2. `infra/Provision-AzureAgent.ps1` — creates the VM, key pair and NSG rule.
   On a restricted subscription, create the VM in the portal instead and record
   its IP in `infra/vm.json`.
3. `tools/step_agent_node.py` — plugin, credential, node, connection.
4. `tools/step_fix_git_tool.py` — the Linux git path override.
5. `tools/step_pipeline_job.py` — creates the job, builds, captures the evidence.

Each script is idempotent: rerunning replaces what it created rather than
duplicating it.
