"""Start a new snapshot dated today. Later API calls cache under this date."""
from pipeline.config import new_snapshot

if __name__ == "__main__":
    print(new_snapshot())
