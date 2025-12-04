# speech-transcriber

## System Architecture
![0](https://github.com/shovonSharma/speech-transcriber/blob/main/0.jpeg)

```bash
speech-transcriber/
├── .dockerignore                  
├── docker-compose.yml             
├── README.md                      
│
├── backend/
│   ├── Dockerfile                 
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── requirements.txt
│   ├── test_api.py
│   ├── db.sqlite                  # ← will be created here automatically
│   └── model/
│       └── vosk-model-small-en-us-0.15/   # ← extract model here 
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js            
│   ├── index.html
│   └── src/
│       ├── main.jsx               
│       ├── App.jsx
│       └── components/
│           ├── StartStop.jsx
│           ├── LivePartial.jsx
│           ├── FinalTranscript.jsx
│           └── Stats.jsx
│
└── venv/                          # ← keep venv, ignored by Docker
```


## User Interface
![1](https://github.com/shovonSharma/speech-transcriber/blob/main/1.png)

## Database
![2](https://github.com/shovonSharma/speech-transcriber/blob/main/2.png)

## Testing
To run tests run

```bash
cd backend
python -m pytest -q
```
and you will see something like this.
![3](https://github.com/shovonSharma/speech-transcriber/blob/main/3.png)
