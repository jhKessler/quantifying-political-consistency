from pathlib import Path

from src.manifestos.download import download_manifestos
from src.votes import build as build_votes
from src.votes.gather import scrape_urls


def check_required_files():
    required_files: dict[str, str] = [
        {
            "path": "input/manifestos.csv",
            "description": "Manifestos CSV file containing urls to party manifestos.",
        }
    ]
    for file in required_files:
        file_path = Path(file["path"])
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file not found: {file_path} - {file['description']}"
            )


def run_preprocessing():
    check_required_files()
    Path("data/").mkdir(exist_ok=True)
    Path("output/").mkdir(exist_ok=True)
    scrape_urls()
    download_manifestos()
    build_votes.build()


if __name__ == "__main__":
    run_preprocessing()
