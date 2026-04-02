pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Lint') {
            steps {
                sh 'flake8 app.py --max-line-length=120 --count --show-source --statistics'
            }
        }

        stage('Test') {
            steps {
                sh 'pytest test_app.py -v'
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build -t aceest-fitness:latest .'
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check the logs.'
        }
    }
}
