// Jenkins Pipeline with JIRA Integration
// Full example for build and deployment tracking

pipeline {
    agent any

    environment {
        JIRA_SITE = 'your-jira-instance'
    }

    stages {
        stage('Build') {
            steps {
                script {
                    // Update JIRA with build info
                    jiraSendBuildInfo(
                        site: env.JIRA_SITE,
                        branch: env.BRANCH_NAME
                    )
                }
                sh 'npm install'
                sh 'npm run build'
            }
        }

        stage('Test') {
            steps {
                sh 'npm test'
            }
        }

        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                sh 'npm run deploy:staging'
                script {
                    jiraSendDeploymentInfo(
                        site: env.JIRA_SITE,
                        environmentId: 'staging',
                        environmentName: 'Staging',
                        environmentType: 'staging',
                        state: 'successful'
                    )
                }
            }
        }

        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                sh 'npm run deploy:production'
                script {
                    jiraSendDeploymentInfo(
                        site: env.JIRA_SITE,
                        environmentId: 'production',
                        environmentName: 'Production',
                        environmentType: 'production',
                        state: 'successful'
                    )
                }
            }
        }
    }

    post {
        always {
            script {
                // Extract JIRA issues from commit messages
                def issues = sh(
                    script: "git log --format=%B -n 1 | grep -oE '[A-Z]+-[0-9]+' | sort -u",
                    returnStdout: true
                ).trim()

                if (issues) {
                    issues.split('\n').each { issue ->
                        jiraComment(
                            issueKey: issue,
                            body: "Build ${currentBuild.result}: ${env.BUILD_URL}"
                        )
                    }
                }
            }
        }

        success {
            script {
                // Optional: Transition issues on success
                if (env.BRANCH_NAME == 'main') {
                    def issues = sh(
                        script: "git log --format=%B -n 1 | grep -oE '[A-Z]+-[0-9]+' | sort -u",
                        returnStdout: true
                    ).trim()

                    issues.split('\n').each { issue ->
                        try {
                            jiraTransitionIssue(
                                idOrKey: issue,
                                input: [transition: [id: '31']] // ID for "Done"
                            )
                        } catch (Exception e) {
                            echo "Could not transition ${issue}: ${e.message}"
                        }
                    }
                }
            }
        }

        failure {
            script {
                // Add flag to issues on failure
                def issues = sh(
                    script: "git log --format=%B -n 1 | grep -oE '[A-Z]+-[0-9]+' | sort -u",
                    returnStdout: true
                ).trim()

                issues.split('\n').each { issue ->
                    jiraComment(
                        issueKey: issue,
                        body: "Build FAILED: ${env.BUILD_URL}\n\nPlease investigate."
                    )
                }
            }
        }
    }
}
