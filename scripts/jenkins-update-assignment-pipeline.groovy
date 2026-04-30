import jenkins.model.Jenkins
import org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition
import org.jenkinsci.plugins.workflow.job.WorkflowJob

def jenkins = Jenkins.instance
def job = jenkins.getItem('assignment-pipeline') as WorkflowJob

if (job == null) {
    throw new RuntimeException('Job assignment-pipeline not found')
}

def pipelineScript = '''
pipeline {
  agent any
  stages {
    stage('Deploy to Local K8s') {
      steps {
        sh ''' + "'''" + '''
          set -e
          kubectl -n aceest rollout restart deployment/aceest-fitness
          kubectl -n aceest rollout status deployment/aceest-fitness --timeout=180s
          kubectl -n aceest get pods -o wide
          kubectl -n aceest get svc aceest-fitness
        ''' + "'''" + '''
      }
    }
  }
  post {
    success { echo 'Deployment via Jenkins completed.' }
    failure { echo 'Deployment failed.' }
  }
}
'''

job.setDefinition(new CpsFlowDefinition(pipelineScript, true))
job.save()

def future = job.scheduleBuild2(0)
if (future == null) {
    throw new RuntimeException('Failed to schedule build')
}

def build = future.get()
println("UPDATED_AND_TRIGGERED_BUILD=${build.number}")
