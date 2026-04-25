// ─────────────────────────────────────────────────────────────────────────────
// ACEest Fitness & Gym — Assignment 2 CI/CD Pipeline
//
// Stages:
//   1. Checkout
//   2. Setup (deps)
//   3. Lint (flake8)
//   4. Unit tests + coverage  (pytest)
//   5. SonarQube static analysis + Quality Gate
//   6. Docker build (image tagged with version + build number)
//   7. Docker Hub push
//   8. Kubernetes deploy (rolling update by default; strategy selectable)
//   9. Smoke test against the deployed Service
//
// Required Jenkins credentials:
//   - dockerhub-creds  (Username with password)
//   - sonar-token      (Secret text)
//   - kubeconfig       (Secret file → ~/.kube/config)
//
// Required Jenkins config:
//   - SonarQube server named 'sonar' pointing at http://sonarqube:9000
//   - Tool 'SonarScanner' (Sonar Scanner installation)
// ─────────────────────────────────────────────────────────────────────────────

pipeline {
    agent any

    parameters {
        string(name: 'APP_VERSION',  defaultValue: 'v3.2.4',  description: 'Application semantic version → image tag')
        choice(name: 'DEPLOY_STRATEGY',
               choices: ['rolling', 'blue-green', 'canary', 'shadow', 'ab-testing', 'none'],
               description: 'Kubernetes deployment strategy to apply')
        booleanParam(name: 'PUSH_IMAGE', defaultValue: true, description: 'Push image to Docker Hub')
    }

    environment {
        DOCKERHUB_USER = 'aceestdevops'                       // ← change to your Docker Hub user
        IMAGE_NAME     = "${DOCKERHUB_USER}/aceest-fitness"
        IMAGE_TAG      = "${params.APP_VERSION}"
        K8S_NAMESPACE  = 'aceest'
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timeout(time: 30, unit: 'MINUTES')
    }

    stages {

        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Setup') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --quiet --upgrade pip
                    pip install --quiet -r requirements.txt
                    pip install --quiet pytest-cov
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '. .venv/bin/activate && flake8 app.py --max-line-length=120 --count --show-source --statistics'
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    . .venv/bin/activate
                    pytest test_app.py -v \
                        --junitxml=pytest-report.xml \
                        --cov=app --cov-report=xml:coverage.xml
                '''
            }
            post {
                always { junit 'pytest-report.xml' }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'
                    withSonarQubeEnv('sonar') {
                        sh "${scannerHome}/bin/sonar-scanner"
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh """
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} \
                                 -t ${IMAGE_NAME}:${BUILD_NUMBER} \
                                 -t ${IMAGE_NAME}:latest .
                """
            }
        }

        stage('Docker Push') {
            when { expression { params.PUSH_IMAGE } }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                                   usernameVariable: 'DH_USER',
                                                   passwordVariable: 'DH_PASS')]) {
                    sh """
                        echo "\$DH_PASS" | docker login -u "\$DH_USER" --password-stdin
                        docker push ${IMAGE_NAME}:${IMAGE_TAG}
                        docker push ${IMAGE_NAME}:${BUILD_NUMBER}
                        docker push ${IMAGE_NAME}:latest
                        docker logout
                    """
                }
            }
        }

        stage('K8s Deploy') {
            when { expression { params.DEPLOY_STRATEGY != 'none' } }
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        kubectl apply -f k8s/base/namespace.yaml
                        STRATEGY_DIR="k8s/${params.DEPLOY_STRATEGY}"
                        for f in \$(find \$STRATEGY_DIR -name '*.yaml'); do
                          sed -e "s|DOCKERHUB_USER|${DOCKERHUB_USER}|g" \
                              -e "s|IMAGE_TAG|${IMAGE_TAG}|g" \$f | kubectl apply -n ${K8S_NAMESPACE} -f -
                        done
                        if [ "${params.DEPLOY_STRATEGY}" = "rolling" ]; then
                          kubectl -n ${K8S_NAMESPACE} rollout status deploy/aceest-rolling --timeout=180s || \
                            (kubectl -n ${K8S_NAMESPACE} rollout undo deploy/aceest-rolling && exit 1)
                        fi
                    """
                }
            }
        }

        stage('Smoke Test') {
            when { expression { params.DEPLOY_STRATEGY != 'none' } }
            steps {
                sh """
                    sleep 10
                    case "${params.DEPLOY_STRATEGY}" in
                      rolling) PORT=30083 ;;
                      blue-green) PORT=30081 ;;
                      canary) PORT=30082 ;;
                      shadow) PORT=30084 ;;
                      ab-testing) PORT=30085 ;;
                      *) PORT=30080 ;;
                    esac
                    curl -fsS "http://localhost:\${PORT}/" | head -c 200 && echo
                """
            }
        }
    }

    post {
        success { echo "Pipeline succeeded — ${IMAGE_NAME}:${IMAGE_TAG} via ${params.DEPLOY_STRATEGY}" }
        failure { echo "Pipeline failed — check stage logs. Use 'kubectl rollout undo' for rollback if needed." }
        always  { sh 'rm -rf .venv || true' }
    }
}
