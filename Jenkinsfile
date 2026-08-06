// Jenkins Lab 2 - build the Maven project on an Azure VM agent node.
//
// Every stage is pinned to the `azure` label, so nothing in this pipeline runs
// on the controller: the checkout, the compile and the packaging all happen on
// the Ubuntu VM in Azure. The "Where am I running" stage exists to prove that
// from the build log rather than asking the reader to take it on trust.
pipeline {
    agent { label 'azure' }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        // The agent has JDK 21 from cloud-init; Maven honours JAVA_HOME.
        JAVA_HOME = '/usr/lib/jvm/java-21-openjdk-amd64'
    }

    stages {
        stage('Where am I running') {
            steps {
                sh '''
                    echo "Jenkins node : $NODE_NAME"
                    echo "Workspace    : $WORKSPACE"
                    echo "Host         : $(hostname)"
                    echo "User         : $(whoami)"
                    echo "Kernel       : $(uname -srm)"
                    echo "Distro       : $(. /etc/os-release && echo $PRETTY_NAME)"
                    echo "Public IP    : $(curl -s --max-time 10 https://api.ipify.org || echo unavailable)"
                '''
            }
        }

        stage('Toolchain') {
            steps {
                sh 'java -version'
                sh 'mvn -version'
                sh 'git --version'
            }
        }

        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log -1 --pretty="commit %H%nauthor %an%ndate   %ad%nsubject %s"'
            }
        }

        stage('Build') {
            steps {
                sh 'mvn -B -ntp clean package'
            }
        }

        stage('Verify artifact') {
            steps {
                sh '''
                    ls -lh target/snake.jar
                    echo "--- manifest ---"
                    unzip -p target/snake.jar META-INF/MANIFEST.MF
                    echo "--- sha256 ---"
                    sha256sum target/snake.jar
                '''
            }
        }

        stage('Archive') {
            steps {
                archiveArtifacts artifacts: 'target/snake.jar', fingerprint: true
            }
        }
    }

    post {
        success {
            echo "SUCCESS - snake.jar was built on ${env.NODE_NAME}, not on the controller."
        }
        always {
            echo "Finished on node: ${env.NODE_NAME}"
        }
    }
}
