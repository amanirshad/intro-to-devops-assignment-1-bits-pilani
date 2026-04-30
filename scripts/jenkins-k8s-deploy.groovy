pipeline {
  agent any

  stages {
    stage('Deploy to Local Kubernetes') {
      steps {
        sh '''
          set -e

          kubectl apply -f - <<'YAML'
apiVersion: v1
kind: Namespace
metadata:
  name: aceest
YAML

          kubectl apply -f - <<'YAML'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aceest-fitness
  namespace: aceest
spec:
  replicas: 2
  selector:
    matchLabels:
      app: aceest-fitness
  template:
    metadata:
      labels:
        app: aceest-fitness
    spec:
      containers:
      - name: aceest-fitness
        image: aceestdevops/aceest-fitness:v3.2.4
        imagePullPolicy: Always
        ports:
        - containerPort: 5000
YAML

          kubectl apply -f - <<'YAML'
apiVersion: v1
kind: Service
metadata:
  name: aceest-fitness
  namespace: aceest
spec:
  selector:
    app: aceest-fitness
  ports:
  - port: 80
    targetPort: 5000
    protocol: TCP
    name: http
  type: NodePort
YAML

          kubectl -n aceest rollout status deployment/aceest-fitness --timeout=180s
          kubectl -n aceest get pods -o wide
          kubectl -n aceest get svc aceest-fitness
        '''
      }
    }
  }

  post {
    success { echo 'Kubernetes deployment completed successfully.' }
    failure { echo 'Deployment failed. Check logs and cluster access.' }
  }
}
