# Jenkins Lab 1

**Goal:** Install Jenkins, then build two projects with it —

1. a **Freestyle project driven by simple commands**, and
2. a **Freestyle project built from a GitHub repository**.

Every step has a screenshot in [`screenshots/`](screenshots), numbered in the order it was performed.

---

## 1. Environment

| Component | Version / location |
|-----------|--------------------|
| OS | Windows 11 Home (10.0.26200) |
| Java (Jenkins runtime) | Eclipse Temurin OpenJDK **21.0.7 LTS** |
| Jenkins | **2.568.1 LTS** (`jenkins.war`) |
| Apache Maven | **3.9.16** — `C:\Users\lokes\tools\apache-maven-3.9.16` |
| Git | 2.47.1.windows.2 |
| `JENKINS_HOME` | `C:\Users\lokes\jenkins-lab\home` |
| Jenkins URL | `http://localhost:8080` (localhost only, never exposed) |

Jenkins requires Java 17 or 21; the machine already had Temurin 21, so no JDK install was needed.

---

## 2. Installing Jenkins

Jenkins was installed using the **official WAR distribution**, which is the install method that
does not require administrator rights and runs on any platform with a supported JDK.

```powershell
# 1. Download the current LTS release (96.4 MB)
Invoke-WebRequest -Uri "https://get.jenkins.io/war-stable/latest/jenkins.war" `
                  -OutFile "C:\Users\lokes\jenkins-lab\jenkins.war"

# 2. Run the controller on port 8080
$env:JENKINS_HOME = "C:\Users\lokes\jenkins-lab\home"
java -jar C:\Users\lokes\jenkins-lab\jenkins.war --httpPort=8080
```

On first start Jenkins generates a one-time administrator password and prints it to the log,
finishing with `Jenkins is fully up and running`.

| # | Screenshot | Step |
|---|-----------|------|
| 1 | [`01-verify-java.png`](screenshots/01-verify-java.png) | Verify the Java prerequisite — `java -version` |
| 2 | [`02-jenkins-startup-initial-password.png`](screenshots/02-jenkins-startup-initial-password.png) | `java -jar jenkins.war` — startup log, one-time admin password, *Jenkins is fully up and running* |

### Setup wizard

Browsing to `http://localhost:8080` starts the post-install wizard.

| # | Screenshot | Step |
|---|-----------|------|
| 3 | [`03-unlock-jenkins.png`](screenshots/03-unlock-jenkins.png) | **Unlock Jenkins** — paste the password from `secrets/initialAdminPassword` |
| 4 | [`04-customize-jenkins.png`](screenshots/04-customize-jenkins.png) | **Customize Jenkins** — chose *Install suggested plugins* |
| 5 | [`05-installing-suggested-plugins.png`](screenshots/05-installing-suggested-plugins.png) | Plugin installation in progress (92 plugins, incl. Git and Maven Integration) |
| 6 | [`06-create-admin-user.png`](screenshots/06-create-admin-user.png) | **Create First Admin User** |
| 7 | [`07-instance-configuration.png`](screenshots/07-instance-configuration.png) | **Instance Configuration** — Jenkins URL `http://localhost:8080/` |
| 8 | [`08-jenkins-is-ready.png`](screenshots/08-jenkins-is-ready.png) | **Jenkins is ready!** |
| 9 | [`09-dashboard-empty.png`](screenshots/09-dashboard-empty.png) | Dashboard after login — no jobs yet |

> The one-time token visible in screenshot 2 is the setup-wizard unlock token. It stops working
> the moment the first admin account is created, and the instance only ever listened on
> `localhost`.

---

## 3. Project 1 — Freestyle project with simple commands

**Job name:** `01-freestyle-simple-commands` · **Config:** [`jobs/01-freestyle-simple-commands/config.xml`](jobs/01-freestyle-simple-commands/config.xml)

Created with **New Item → Freestyle project**, with a single build step of type
**Execute Windows batch command**:

```bat
@echo off
echo ==================================================
echo   Freestyle Project 1 - Simple Commands
echo ==================================================
echo Job name     : %JOB_NAME%
echo Build number : %BUILD_NUMBER%
echo Build tag    : %BUILD_TAG%
echo Workspace    : %WORKSPACE%
echo Executed on  : %NODE_NAME%

echo --- 1. Date and time ---
date /t
time /t

echo --- 2. Current working directory ---
cd

echo --- 3. Java version available to the build ---
java -version

echo --- 4. Write a file into the workspace, then read it back ---
echo Hello from Jenkins build #%BUILD_NUMBER% > greeting.txt
type greeting.txt

echo --- 5. Workspace contents ---
dir /b

echo Build completed successfully.
```

The step demonstrates that a freestyle job runs ordinary shell commands, can read Jenkins'
injected environment variables (`JOB_NAME`, `BUILD_NUMBER`, `BUILD_TAG`, `WORKSPACE`, `NODE_NAME`),
and has a writable per-job workspace.

| # | Screenshot | Step |
|---|-----------|------|
| 10 | [`10-new-item-freestyle-project.png`](screenshots/10-new-item-freestyle-project.png) | New Item → name entered, **Freestyle project** selected |
| 11 | [`11-job1-config-build-step.png`](screenshots/11-job1-config-build-step.png) | Build step — *Execute Windows batch command* with the script |
| 12 | [`12-job1-project-page.png`](screenshots/12-job1-project-page.png) | Project page after **Build Now** — build #1 in the history |
| 13 | [`13-job1-console-output.png`](screenshots/13-job1-console-output.png) | **Console Output** — every command's output, `Finished: SUCCESS` |

**Result: `SUCCESS`** in 1.2 s. Full log: [`logs/01-freestyle-simple-commands-build-1.log`](logs/01-freestyle-simple-commands-build-1.log)

---

## 4. Project 2 — Freestyle project built from GitHub

**Job name:** `02-freestyle-github-snake-game` · **Config:** [`jobs/02-freestyle-github-snake-game/config.xml`](jobs/02-freestyle-github-snake-game/config.xml)

This job checks out a real GitHub repository and builds it with Maven.

| Setting | Value |
|---------|-------|
| Source Code Management | **Git** |
| Repository URL | `https://github.com/Lokesh7025/devops.git` |
| Credentials | *none* (public repository) |
| Branch specifier | `*/main` |
| Build step | **Invoke top-level Maven targets** |
| Maven Version | `Maven-3.9.16` |
| Goals | `clean package` |
| Post-build action | **Archive the artifacts** → `target/*.jar` |

The project on `main` is `com.snake:snake-game:1.0-SNAPSHOT`, which uses the
`maven-shade-plugin` to produce an executable fat JAR named `snake.jar`.

### Registering Maven as a Jenkins tool

Before the job could use *Invoke top-level Maven targets*, Maven was registered under
**Manage Jenkins → Tools**. *Install automatically* was unchecked so Jenkins uses the Maven
already installed on the machine rather than downloading its own copy.

| # | Screenshot | Step |
|---|-----------|------|
| 14 | [`14-global-tool-config-maven.png`](screenshots/14-global-tool-config-maven.png) | **Tools** — Maven installation `Maven-3.9.16`, `MAVEN_HOME` set to the local install |
| 15 | [`15-new-item-freestyle-github.png`](screenshots/15-new-item-freestyle-github.png) | New Item → second **Freestyle project** |
| 16 | [`16-job2-config-git-scm.png`](screenshots/16-job2-config-git-scm.png) | **Source Code Management → Git** — repository URL and branch `*/main` |
| 17 | [`17-job2-config-maven-step.png`](screenshots/17-job2-config-maven-step.png) | Build step *Invoke top-level Maven targets* (`clean package`) + *Archive the artifacts* |
| 18 | [`18-job2-project-page.png`](screenshots/18-job2-project-page.png) | Project page after **Build Now** |
| 19 | [`19-job2-console-output.png`](screenshots/19-job2-console-output.png) | Console output — `git.exe fetch` / `checkout`, then Maven starting |
| 20 | [`20-job2-build-success.png`](screenshots/20-job2-build-success.png) | End of the console output — `BUILD SUCCESS`, `Archiving artifacts`, `Finished: SUCCESS` |
| 21 | [`21-job2-archived-artifact.png`](screenshots/21-job2-archived-artifact.png) | Build #1 page — archived artifact `snake.jar` (572.56 KiB) |
| 22 | [`22-dashboard-both-jobs.png`](screenshots/22-dashboard-both-jobs.png) | Dashboard — both freestyle projects, both passing |

### What the build did

```
Cloning repository https://github.com/Lokesh7025/devops.git
 > git.exe fetch --tags --force --progress -- https://github.com/Lokesh7025/devops.git ...
Checking out Revision 0a3a96f27990a09acd8e1c3ad263e39bd7ca58ad (refs/remotes/origin/main)
Commit message: "fix"
[02-freestyle-github-snake-game] $ cmd.exe /C "C:\Users\lokes\tools\apache-maven-3.9.16\bin\mvn.cmd clean package && exit %%ERRORLEVEL%%"
...
[INFO] Including com.googlecode.lanterna:lanterna:jar:3.1.1 in the shaded jar.
[INFO] Replacing original artifact with shaded artifact.
[INFO] BUILD SUCCESS
[INFO] Total time:  13.766 s
Archiving artifacts
Finished: SUCCESS
```

**Result: `SUCCESS`** in 30 s, artifact `snake.jar` archived.
Full log: [`logs/02-freestyle-github-snake-game-build-1.log`](logs/02-freestyle-github-snake-game-build-1.log)

---

## 5. Comparing the two jobs

| | Project 1 | Project 2 |
|---|-----------|-----------|
| Source | none — commands only | Git clone from GitHub |
| Build step type | Execute Windows batch command | Invoke top-level Maven targets |
| External tools | none | Git plugin, Maven 3.9.16 |
| Produces artifacts | no | yes — `snake.jar`, archived |
| Duration | 1.2 s | 30 s (includes dependency download) |

Project 1 shows the mechanics of a freestyle job in isolation: workspace, environment variables,
and serial build steps. Project 2 adds the two pieces that make Jenkins a CI server — pulling
source from a remote SCM, and turning it into a versioned, archived build artifact.

---

## 6. Reproducing this lab

`tools/` holds the scripts used to perform and capture the lab:

| File | Purpose |
|------|---------|
| `Start-Jenkins.ps1` | Launches the controller in a console window with `JENKINS_HOME` set |
| `Capture-Window.ps1` | Screenshots a native window by title (used for the terminal captures) |
| `Show-Step.ps1` | Runs a command in a fresh console window and captures it |
| `cdp.py` | Minimal Chrome DevTools Protocol driver — clicks, form fills and PNG capture |
| `step1_wizard.py`, `step1b_wizard.py` | Drive the setup wizard |
| `step2`–`step5` | Create, configure, save and build project 1 |
| `step6`–`step11` | Register Maven, then create, configure, build and capture project 2 |

The admin credentials are read from `JENKINS_ADMIN_USER` / `JENKINS_ADMIN_PASS` environment
variables, so no password is stored in this repository.

---

## 7. Folder contents

```
jenkins-lab-1/
├── README.md                 this report
├── screenshots/              22 screenshots, numbered in execution order
├── jobs/                     exported config.xml for both freestyle projects
├── logs/                     full console logs of build #1 of each project
└── tools/                    scripts used to install, drive and capture the lab
```
