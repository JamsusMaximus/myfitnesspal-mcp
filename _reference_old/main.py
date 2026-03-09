import argparse
from nutrition_coach.api_server import run_server

def main():
    parser = argparse.ArgumentParser(description="Nutrition Coach API Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on (default: 8000)")
    args = parser.parse_args()
    
    run_server(port=args.port)


if __name__ == "__main__":
    main()
