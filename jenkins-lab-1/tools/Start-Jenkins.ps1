# Launches the Jenkins controller in its own visible console window so the
# startup log (including the initial admin password) can be screenshotted.
$Host.UI.RawUI.WindowTitle = 'JENKINS-SERVER'
try {
    $Host.UI.RawUI.BufferSize = New-Object Management.Automation.Host.Size(118, 5000)
    $Host.UI.RawUI.WindowSize  = New-Object Management.Automation.Host.Size(118, 34)
} catch { }

$env:JENKINS_HOME = 'C:\Users\lokes\jenkins-lab\home'
Set-Location 'C:\Users\lokes\jenkins-lab'

Write-Host '=== STEP 2: Start Jenkins (java -jar jenkins.war --httpPort=8080) ===' -ForegroundColor Cyan
java -jar C:\Users\lokes\jenkins-lab\jenkins.war --httpPort=8080
