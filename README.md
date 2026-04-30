# ACEest Fitness & Gym

A Flask-based web application for ACEest Fitness & Gym management, featuring fitness program details, calorie estimation, and BMI calculation.

## Features

- Browse fitness programs (Fat Loss, Muscle Gain, Beginner)
- Calculate daily calorie targets based on weight and program
- BMI calculator with category classification
- Member registration and listing
- Health check endpoint

## Project Structure

```
├── app.py                       # Flask application
├── test_app.py                  # Pytest test suite
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container configuration
├── Jenkinsfile                  # Jenkins pipeline (Assignment 2 — full CI/CD)
├── sonar-project.properties     # SonarQube scanner config
├── docker-compose.ci.yml        # Local Jenkins + SonarQube stack
├── scripts/
│   ├── setup-local-ci.sh        # Bootstraps Jenkins + SonarQube on macOS
│   └── teardown-local-ci.sh
├── k8s/                         # Kubernetes manifests (Assignment 2)
│   ├── base/                    # Namespace + default deployment + service
│   ├── rolling/                 # Rolling-update strategy
│   ├── blue-green/              # Blue-green strategy + switch.sh
│   ├── canary/                  # Canary release strategy
│   ├── shadow/                  # Shadow deployment via nginx mirror
│   └── ab-testing/              # Header-based A/B routing via nginx
├── code-versions/               # Versioned legacy app revisions (v1.0 … v3.2.4)
├── REPORT.md                    # Assignment 2 CI/CD report
├── .github/workflows/main.yml   # GitHub Actions (Assignment 1)
└── README.md
```

## Assignment 2 — Full CI/CD on Local Kubernetes

The Assignment 2 deliverable extends the project with Jenkins-driven CI/CD,
SonarQube quality gates, Docker Hub publication, and Kubernetes deployments
with all five rollout strategies (rolling, blue-green, canary, shadow, A/B).

### Local infrastructure (macOS, Apple Silicon, Docker Desktop K8s)

```bash
# 1. Start the local stack (Jenkins:8080, SonarQube:9000)
chmod +x scripts/*.sh k8s/blue-green/switch.sh
./scripts/setup-local-ci.sh

# 2. Configure Jenkins (one-time, see scripts/setup-local-ci.sh output)
#    - Install plugins: Docker Pipeline, SonarQube Scanner, Kubernetes CLI
#    - Add credentials: dockerhub-creds, sonar-token, kubeconfig
#    - SonarQube server name: 'sonar', URL: http://sonarqube:9000

# 3. Create a Jenkins Pipeline job pointing at this repo (script path: Jenkinsfile)
#    Build with parameters → choose APP_VERSION + DEPLOY_STRATEGY.
```

### Deployment strategies

See [k8s/README.md](k8s/README.md). Each strategy is exposed on its own NodePort:

| Strategy   | URL                          |
|------------|------------------------------|
| Rolling    | http://localhost:30083        |
| Blue-Green | http://localhost:30081        |
| Canary     | http://localhost:30082        |
| Shadow     | http://localhost:30084        |
| A/B        | http://localhost:30085 (`X-Variant: A\|B`) |

### Rollback

* Rolling — `kubectl -n aceest rollout undo deploy/aceest-rolling`
* Blue-Green — `./k8s/blue-green/switch.sh blue`
* Canary — `kubectl -n aceest scale deploy/aceest-canary --replicas=0`

Full architecture, challenges and outcomes are documented in [REPORT.md](REPORT.md).

## Local Setup & Execution

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/aceest-fitness.git
cd aceest-fitness

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The app will be available at `http://localhost:5000`.

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page |
| GET | `/programs` | List all fitness programs |
| GET | `/programs/<key>` | Get program details |
| POST | `/calculate/calories` | Calculate daily calories |
| POST | `/calculate/bmi` | Calculate BMI |
| GET | `/members` | List members |
| POST | `/members` | Add a new member |
| GET | `/health` | Health check |

### Example API Calls

```bash
# Get calorie estimate
curl -X POST http://localhost:5000/calculate/calories \
  -H "Content-Type: application/json" \
  -d '{"weight": 80, "program": "fat_loss"}'

# Calculate BMI
curl -X POST http://localhost:5000/calculate/bmi \
  -H "Content-Type: application/json" \
  -d '{"weight": 70, "height": 175}'

# Add a member
curl -X POST http://localhost:5000/members \
  -H "Content-Type: application/json" \
  -d '{"name": "Ravi", "program": "muscle_gain"}'
```

## Running Tests

```bash
# Run all tests
pytest test_app.py -v

# Run with coverage (install pytest-cov first)
pytest test_app.py -v --tb=short
```

## Docker

```bash
# Build the image
docker build -t aceest-fitness:latest .

# Run the container
docker run -p 5000:5000 aceest-fitness:latest

# Run tests inside the container
docker run --rm aceest-fitness:latest pytest test_app.py -v
```

## CI/CD Pipeline

### GitHub Actions

The pipeline (`.github/workflows/main.yml`) is triggered on every `push` or `pull_request` to the `main` branch and performs:

1. **Build & Lint** – Installs dependencies and runs `flake8` for syntax/style checks.
2. **Automated Testing** – Runs the full `pytest` suite.
3. **Docker Image Assembly** – Builds the Docker image and runs tests inside the container.

### Jenkins Integration

The `Jenkinsfile` defines a pipeline with the following stages:

1. **Checkout** – Pulls the latest code from the repository.
2. **Setup** – Installs Python dependencies.
3. **Lint** – Runs flake8 code quality checks.
4. **Test** – Executes pytest suite.
5. **Docker Build** – Builds the Docker image.

To configure Jenkins:

1. Install Jenkins and the Pipeline plugin.
2. Create a new Pipeline project.
3. Point the pipeline to this repository.
4. Jenkins will automatically detect the `Jenkinsfile` and run the stages.

## Tech Stack

- **Backend**: Flask (Python)
- **Testing**: Pytest
- **Linting**: Flake8
- **Containerization**: Docker
- **CI/CD**: GitHub Actions + Jenkins
