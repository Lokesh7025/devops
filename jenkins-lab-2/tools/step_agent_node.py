"""Attach the Azure VM to Jenkins as an SSH agent node, and capture it.

Three things happen here:

  1. the SSH Build Agents plugin is installed if it is missing;
  2. the agent's private key is registered as a Jenkins credential;
  3. a permanent node is created that launches over SSH and carries the
     `azure` label the pipeline asks for.

Steps 2 and 3 go through the Jenkins script console rather than the web forms.
That is a deliberate choice for the credential in particular: Jenkins reads the
private key off disk itself, so the key never passes through a browser form
being driven by automation. The resulting configuration is then screenshotted
from the ordinary UI pages, which show exactly what a human would have filled
in by hand.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jenkins as J

VM = json.load(open(r"C:\Users\lokes\jenkins-lab\lab2\vm.json", encoding="utf-8-sig"))
HOST = VM["publicIp"]
KEY = VM["keyFile"].replace("\\", "/")
USER = VM["adminUser"]
CRED_ID = "azure-agent-ssh"
NODE = "azure-agent-1"
REMOTE_ROOT = f"/home/{USER}/jenkins"
LABELS = "azure linux"

PLUGIN = "ssh-slaves"


def has_plugin(b, short_name):
    out = J.groovy(b, f"""
        println(Jenkins.instance.pluginManager.getPlugin('{short_name}') ? 'YES' : 'NO')
    """)
    return "YES" in (out or "")


def install_plugin(b, short_name):
    print(f"installing plugin {short_name}", flush=True)
    J.groovy(b, f"""
        def pm = Jenkins.instance.pluginManager
        def uc = Jenkins.instance.updateCenter
        if (uc.getPlugin('{short_name}') == null) {{ uc.updateAllSites() }}
        def f = uc.getPlugin('{short_name}').deploy(true)
        f.get()
        println('deployed')
    """, timeout=600)
    # A dynamic load usually avoids a restart, but not always; poll for it.
    for _ in range(60):
        if has_plugin(b, short_name):
            return True
        time.sleep(5)
    return False


def main():
    b = J.connect_jenkins()
    try:
        # -- 1. plugin -------------------------------------------------------
        if has_plugin(b, PLUGIN):
            print(f"plugin {PLUGIN} already present", flush=True)
        else:
            if not install_plugin(b, PLUGIN):
                raise RuntimeError(f"{PLUGIN} did not come up; a restart is needed")

        b.goto(J.JENKINS + "/manage/pluginManager/installed?filter=ssh", wait_ms=2500)
        J.shot(b, "10-jenkins-ssh-plugin.png",
               "The SSH Build Agents plugin, which provides the SSH launcher")

        # -- 2. credential ---------------------------------------------------
        out = J.groovy(b, f"""
            import com.cloudbees.plugins.credentials.*
            import com.cloudbees.plugins.credentials.domains.Domain
            import com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey

            def store = SystemCredentialsProvider.getInstance().getStore()
            def existing = store.getCredentials(Domain.global()).find {{ it.id == '{CRED_ID}' }}
            if (existing) {{
                println('credential already exists')
            }} else {{
                def key = new File('{KEY}').getText('UTF-8')
                def src = new BasicSSHUserPrivateKey.DirectEntryPrivateKeySource(key)
                def c = new BasicSSHUserPrivateKey(
                    CredentialsScope.GLOBAL, '{CRED_ID}', '{USER}', src, '',
                    'SSH key for the Azure Jenkins agent')
                store.addCredentials(Domain.global(), c)
                println('credential created')
            }}
        """)
        print("credential:", (out or "").strip()[:200], flush=True)

        b.goto(J.JENKINS + "/manage/credentials/store/system/domain/_/", wait_ms=2500)
        J.shot(b, "11-jenkins-credential.png",
               "The SSH private key registered as a Jenkins credential")

        # -- 3. the node -----------------------------------------------------
        out = J.groovy(b, f"""
            import hudson.model.Node
            import hudson.plugins.sshslaves.SSHLauncher
            import hudson.plugins.sshslaves.verifiers.NonVerifyingKeyVerificationStrategy
            import hudson.slaves.DumbSlave
            import hudson.slaves.RetentionStrategy

            def j = Jenkins.instance
            j.nodes.findAll {{ it.nodeName == '{NODE}' }}.each {{ j.removeNode(it) }}

            def launcher = new SSHLauncher('{HOST}', 22, '{CRED_ID}')
            launcher.setSshHostKeyVerificationStrategy(new NonVerifyingKeyVerificationStrategy())
            launcher.setLaunchTimeoutSeconds(120)
            launcher.setMaxNumRetries(5)
            launcher.setRetryWaitTime(20)

            def node = new DumbSlave('{NODE}', '{REMOTE_ROOT}', launcher)
            node.setNodeDescription('Ubuntu 24.04 VM in Microsoft Azure ({VM["vmSize"]}, {VM["location"]})')
            node.setNumExecutors(1)
            node.setLabelString('{LABELS}')
            node.setMode(Node.Mode.NORMAL)
            node.setRetentionStrategy(new RetentionStrategy.Always())
            j.addNode(node)
            println('node created')
        """)
        print("node:", (out or "").strip()[:200], flush=True)

        # -- 4. bring it online ----------------------------------------------
        print("waiting for the agent to connect", flush=True)
        online = False
        for i in range(60):
            state = J.groovy(b, f"""
                def c = Jenkins.instance.getComputer('{NODE}')
                if (c == null) {{ println('MISSING') }}
                else if (c.isOnline()) {{ println('ONLINE') }}
                else {{
                    if (c.isOffline() && !c.isConnecting()) {{ c.connect(false) }}
                    println('OFFLINE')
                }}
            """, timeout=180) or ""
            if "ONLINE" in state:
                online = True
                print(f"agent online after {i * 10}s", flush=True)
                break
            time.sleep(10)

        b.goto(J.JENKINS + f"/computer/{NODE}/log", wait_ms=2500)
        J.shot(b, "12-agent-connection-log.png",
               "The agent connection log - Jenkins launching remoting over SSH")

        b.goto(J.JENKINS + "/computer/", wait_ms=2500)
        J.shot(b, "13-jenkins-nodes.png",
               "The Nodes page: the built-in node plus the Azure agent")

        b.goto(J.JENKINS + f"/computer/{NODE}/", wait_ms=2500)
        J.shot(b, "14-agent-overview.png",
               "The Azure agent node - labels, executor and remote root")

        b.goto(J.JENKINS + f"/computer/{NODE}/configure", wait_ms=3000)
        J.shot(b, "15-agent-configure.png",
               "The node configuration: SSH launch method, host, credential")

        b.goto(J.JENKINS + f"/computer/{NODE}/systemInfo", wait_ms=2500)
        J.shot(b, "16-agent-system-info.png",
               "System information reported by the agent - a Linux JVM in Azure")

        if not online:
            raise RuntimeError("the agent never came online; see 12-agent-connection-log.png")
        print("OK - agent is online", flush=True)
    finally:
        b.close(keep_browser=True)


if __name__ == "__main__":
    main()
