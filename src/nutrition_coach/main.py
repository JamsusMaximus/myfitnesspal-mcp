import argparse
from nutrition_coach import myfitnesspal_scraper
from nutrition_coach.api_server import run_server


def main():
    parser = argparse.ArgumentParser(description="Nutrition Coach API Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on (default: 8000)")
    parser.add_argument("--scrape", action="store_true", help="Run the MyFitnessPal scraper")
    args = parser.parse_args()
    
    if args.scrape:
        myfitnesspal_scraper.run_scraper_sync()
    else:
        run_server(port=args.port)

if __name__ == "__main__":
    main()
