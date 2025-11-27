# strava-counter-almas-inquietas
Data retriever for Almas Inquietas org.


Project structure:

strava-counter-almas-inquietas/
│
├── .github/
│   └── workflows/
│       ├── deploy-worker.yml   # Deploy strava data retriever lambda
│       ├── deploy-api.yml      # Deploy backend in a lambda
│       └── deploy-frontend.yml # Deploy web frontend
│
├── worker/
│   └── lambda_function.py      # Strava data retreiver source code
│
├── api/
│   └── lambda_function.py      # Read data from DynamoBD and process it to send it formated for the frontend
│
└── frontend/
    ├── public/
    ├── src/
    │   ├── components/
    │   └── App.jsx
    ├── package.json
    └── ...