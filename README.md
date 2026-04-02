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
├── app.py                  # Flask application
├── test_app.py             # Pytest test suite
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container configuration
├── Jenkinsfile             # Jenkins pipeline definition
├── .github/
│   └── workflows/
│       └── main.yml        # GitHub Actions CI/CD pipeline
└── README.md
```

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
