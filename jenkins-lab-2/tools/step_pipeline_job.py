"""Create the pipeline job, run it on the Azure agent, and capture the proof.

The job is a Pipeline reading its Jenkinsfile from SCM, which is what makes the
`agent { label 'azure' }` line authoritative: the stages are defined in the
repository, not in the Jenkins UI, so the build cannot quietly fall back to the
controller.
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jenkins as J

JOB = "snake-game-on-azure-agent"
# SSH rather than HTTPS: the repository is private and the agent is a Linux VM
# with no credential helper, so the checkout needs a key it can present. A
# read-only deploy key is the narrowest thing that works - it grants access to
# this one repository and nothing else on the account.
REPO = "git@github.com:Lokesh7025/devops.git"
BRANCH = "*/jenkins-lab-2"
NODE = "azure-agent-1"
LOGS = r"C:\Users\lokes\jenkins-lab\lab2\logs"

SCM_CREDENTIAL = "github-deploy-key"
DEPLOY_KEY = r"C:\Users\lokes\jenkins-lab\lab2\ssh\github_deploy_key".replace("\\", "/")


def setup_scm_credential(b):
    """Registers the deploy key and lets git trust GitHub's host key.

    Both the controller (reading the Jenkinsfile) and the agent (running
    `checkout scm`) clone over SSH, so the host key has to be acceptable on
    both. 'Accept first connection' pins whatever GitHub presents on the first
    clone and rejects any change after that - weaker than shipping a known_hosts
    file, stronger than disabling the check outright.
    """
    out = J.groovy(b, f"""
        import com.cloudbees.plugins.credentials.*
        import com.cloudbees.plugins.credentials.domains.Domain
        import com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey

        def store = SystemCredentialsProvider.getInstance().getStore()
        if (store.getCredentials(Domain.global()).find {{ it.id == '{SCM_CREDENTIAL}' }}) {{
            println('deploy key credential already exists')
        }} else {{
            def key = new File('{DEPLOY_KEY}').getText('UTF-8')
            store.addCredentials(Domain.global(), new BasicSSHUserPrivateKey(
                CredentialsScope.GLOBAL, '{SCM_CREDENTIAL}', 'git',
                new BasicSSHUserPrivateKey.DirectEntryPrivateKeySource(key), '',
                'Read-only GitHub deploy key for Lokesh7025/devops'))
            println('deploy key credential created')
        }}

        try {{
            def cls = this.class.classLoader.loadClass(
                'org.jenkinsci.plugins.gitclient.verifier.GitHostKeyVerificationConfiguration')
            def cfg = jenkins.model.GlobalConfiguration.all().get(cls)
            def strat = this.class.classLoader.loadClass(
                'org.jenkinsci.plugins.gitclient.verifier.AcceptFirstConnectionStrategy')
            cfg.setSshHostKeyVerificationStrategy(strat.newInstance())
            cfg.save()
            println('host key strategy: accept first connection')
        }} catch (e) {{
            println('host key strategy unchanged: ' + e)
        }}
    """)
    print("scm credential:", (out or "").strip()[:300], flush=True)


def config_xml():
    cred = (f"<credentialsId>{SCM_CREDENTIAL}</credentialsId>"
            if SCM_CREDENTIAL else "")
    return f"""<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <description>Builds the Maven project on the Azure VM agent node (Jenkins Lab 2).</description>
  <keepDependencies>false</keepDependencies>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps">
    <scm class="hudson.plugins.git.GitSCM" plugin="git">
      <configVersion>2</configVersion>
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>{REPO}</url>
          {cred}
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>{BRANCH}</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
      <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
      <extensions/>
    </scm>
    <scriptPath>Jenkinsfile</scriptPath>
    <lightweight>false</lightweight>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
"""


def create_job(b):
    xml = config_xml()
    return b.eval("""(async () => {
      const c = await (await fetch('/crumbIssuer/api/json',{credentials:'same-origin'})).json();
      const h = {'Content-Type':'application/xml'}; h[c.crumbRequestField]=c.crumb;
      const body = %s;
      let r = await fetch('/createItem?name=%s', {method:'POST',credentials:'same-origin',headers:h,body});
      if (r.status === 400) {   // already exists - update it instead
        r = await fetch('/job/%s/config.xml', {method:'POST',credentials:'same-origin',headers:h,body});
        return 'updated ' + r.status;
      }
      return 'created ' + r.status;
    })()""" % (json.dumps(xml), JOB, JOB), timeout=180)


def build(b):
    """Triggers a build and returns its number once it has finished."""
    before = b.eval(f"""(async () => {{
      const r = await fetch('/job/{JOB}/api/json?tree=nextBuildNumber',{{credentials:'same-origin'}});
      return (await r.json()).nextBuildNumber;
    }})()""")
    J.post_form(b, f"/job/{JOB}/build", {"delay": "0sec"})
    print(f"triggered build #{before}", flush=True)

    for _ in range(180):
        info = b.eval(f"""(async () => {{
          const r = await fetch('/job/{JOB}/{before}/api/json?tree=building,result',
                                {{credentials:'same-origin'}});
          if (!r.ok) return null;
          const j = await r.json();
          return j.building ? 'BUILDING' : (j.result || 'UNKNOWN');
        }})()""")
        if info and info not in ("BUILDING",):
            return before, info
        time.sleep(10)
    return before, "TIMEOUT"


def main():
    b = J.connect_jenkins()
    os.makedirs(LOGS, exist_ok=True)
    try:
        setup_scm_credential(b)
        b.goto(J.JENKINS + "/manage/credentials/store/system/domain/_/", wait_ms=3000)
        J.shot(b, "11-jenkins-credential.png",
               "Both credentials: the agent's SSH key and the repo deploy key")

        print("job:", create_job(b), flush=True)

        b.goto(f"{J.JENKINS}/job/{JOB}/configure", wait_ms=3500)
        J.shot(b, "17-pipeline-job-config.png",
               "The pipeline job: definition read from the repository")

        # Kick it off, then grab a shot while it is genuinely mid-flight.
        num = b.eval(f"""(async () => {{
          const r = await fetch('/job/{JOB}/api/json?tree=nextBuildNumber',{{credentials:'same-origin'}});
          return (await r.json()).nextBuildNumber;
        }})()""")
        J.post_form(b, f"/job/{JOB}/build", {"delay": "0sec"})
        print(f"triggered build #{num}", flush=True)

        for _ in range(30):
            live = b.eval(f"""(async () => {{
              const r = await fetch('/job/{JOB}/{num}/api/json?tree=building',
                                    {{credentials:'same-origin'}});
              return r.ok ? (await r.json()).building : null;
            }})()""")
            if live:
                break
            time.sleep(2)

        b.goto(f"{J.JENKINS}/job/{JOB}/{num}/console", wait_ms=6000)
        J.shot(b, "18-build-in-progress.png",
               f"Build #{num} in flight on the Azure agent")

        # Wait it out.
        result = "UNKNOWN"
        for _ in range(180):
            r = b.eval(f"""(async () => {{
              const x = await fetch('/job/{JOB}/{num}/api/json?tree=building,result',
                                    {{credentials:'same-origin'}});
              if (!x.ok) return null;
              const j = await x.json();
              return j.building ? 'BUILDING' : (j.result || 'UNKNOWN');
            }})()""")
            if r and r != "BUILDING":
                result = r
                break
            time.sleep(10)
        print(f"build #{num} finished: {result}", flush=True)

        # -- save the console log to disk ------------------------------------
        text = b.eval(f"""(async () => {{
          const r = await fetch('/job/{JOB}/{num}/consoleText',{{credentials:'same-origin'}});
          return await r.text();
        }})()""", timeout=180) or ""
        path = os.path.join(LOGS, f"build-{num}-console.txt")
        open(path, "w", encoding="utf-8").write(text)
        print(f"saved {path} ({len(text)} bytes)", flush=True)

        ran_on = re.search(r"Running on (\S+) in (\S+)", text)
        if ran_on:
            print(f"ran on node: {ran_on.group(1)}  workspace: {ran_on.group(2)}", flush=True)

        # -- captures --------------------------------------------------------
        b.goto(f"{J.JENKINS}/job/{JOB}/{num}/console", wait_ms=4000)
        b.eval("window.scrollTo(0,0); 1")
        J.shot(b, "19-build-console-top.png",
               "Console log - the checkout and the node it is running on",
               max_height=4200)

        b.goto(f"{J.JENKINS}/job/{JOB}/{num}/", wait_ms=3500)
        J.shot(b, "20-build-result.png",
               f"Build #{num} result page with the archived artifact")

        b.goto(f"{J.JENKINS}/job/{JOB}/", wait_ms=4000)
        J.shot(b, "21-pipeline-stage-view.png",
               "Stage view - every stage ran on the Azure agent")

        b.goto(f"{J.JENKINS}/computer/{NODE}/builds", wait_ms=3000)
        J.shot(b, "22-agent-build-history.png",
               "Build history recorded against the Azure agent node")

        if result != "SUCCESS":
            raise SystemExit(f"build result was {result}, not SUCCESS")
    finally:
        b.close(keep_browser=True)


if __name__ == "__main__":
    main()
