"""Teach Jenkins where git lives on the Linux agent.

Lab 1 configured the Git tool as `git.exe`, which is right for the Windows
controller and meaningless on Ubuntu, so the first build died at
`Cannot run program "git.exe"`. Rather than change the global tool and break
the Windows side, this adds a *node-level tool location* on the agent: same
tool, different path per machine, which is exactly what that Jenkins feature
exists for.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jenkins as J

NODE = "azure-agent-1"
GIT_ON_AGENT = "/usr/bin/git"


def main():
    b = J.connect_jenkins()
    try:
        print("--- git tool installations before ---", flush=True)
        print(J.groovy(b, """
            def d = Jenkins.instance.getDescriptorByType(
                hudson.plugins.git.GitTool.DescriptorImpl.class)
            d.installations.each { println("  ${it.name} -> ${it.home}") }
            if (!d.installations) println('  (none configured)')
        """), flush=True)

        out = J.groovy(b, f"""
            import hudson.tools.ToolLocationNodeProperty
            import hudson.plugins.git.GitTool

            def node = Jenkins.instance.getNode('{NODE}')
            def desc = Jenkins.instance.getDescriptorByType(GitTool.DescriptorImpl.class)

            // Make sure a named installation exists to bind the override to.
            if (!desc.installations) {{
                desc.installations = [new GitTool('Default', 'git', null)] as GitTool[]
                desc.save()
            }}
            def toolName = desc.installations[0].name

            def locs = desc.installations.collect {{
                new ToolLocationNodeProperty.ToolLocation(desc, it.name, '{GIT_ON_AGENT}')
            }}
            node.nodeProperties.removeAll(ToolLocationNodeProperty.class)
            node.nodeProperties.add(new ToolLocationNodeProperty(locs))
            Jenkins.instance.updateNode(node)
            println("bound git tool '" + toolName + "' to {GIT_ON_AGENT} on {NODE}")
        """)
        print("fix:", (out or "").strip()[:300], flush=True)

        b.goto(f"{J.JENKINS}/computer/{NODE}/configure", wait_ms=4000)
        J.shot(b, "15-agent-configure.png",
               "Node configuration - SSH launcher plus the Linux git tool location")
    finally:
        b.close(keep_browser=True)


if __name__ == "__main__":
    main()
