cd backend
uvicorn server:app --reload --host 0.0.0.0 --port 8000

cd frontend
python3 client_pyqt.py