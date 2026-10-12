pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Unit Tests') {
            steps {
                bat 'python -m venv .venv'
                bat '.venv\\Scripts\\python -m pip install --upgrade pip'
                bat '.venv\\Scripts\\python -m pip install -r requirements.txt'
                bat '.venv\\Scripts\\python -m pytest -v --junitxml=test-reports\\junit.xml'
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-reports/junit.xml'
                }
            }
        }

        stage('Docker Build') {
            steps {
                bat 'docker build -t eventease:latest .'
            }
        }

        stage('Deploy') {
            steps {
                bat 'docker compose up -d --build'
                bat 'docker compose ps'
            }
        }

        stage('Smoke Test') {
            steps {
                bat 'powershell -NoProfile -ExecutionPolicy Bypass -File scripts\\smoke_test.ps1'
            }
        }
    }

    post {
        success { echo 'EventEase pipeline finished: SUCCESS' }
        failure { echo 'EventEase pipeline FAILED - see the stage above' }
    }
}
