"""
Script to download the full KJV Bible and prepare it for indexing.
Downloads from a public GitHub repository with structured Bible data.
"""
import os
import sys
import json
import requests
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# KJV Bible JSON source (public domain)
BIBLE_URL = "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/en_kjv.json"

# Book name mapping for cleaner names
BOOK_NAMES = {
    1: "Genesis", 2: "Exodus", 3: "Leviticus", 4: "Numbers", 5: "Deuteronomy",
    6: "Joshua", 7: "Judges", 8: "Ruth", 9: "1 Samuel", 10: "2 Samuel",
    11: "1 Kings", 12: "2 Kings", 13: "1 Chronicles", 14: "2 Chronicles",
    15: "Ezra", 16: "Nehemiah", 17: "Esther", 18: "Job", 19: "Psalms",
    20: "Proverbs", 21: "Ecclesiastes", 22: "Song of Solomon", 23: "Isaiah",
    24: "Jeremiah", 25: "Lamentations", 26: "Ezekiel", 27: "Daniel",
    28: "Hosea", 29: "Joel", 30: "Amos", 31: "Obadiah", 32: "Jonah",
    33: "Micah", 34: "Nahum", 35: "Habakkuk", 36: "Zephaniah", 37: "Haggai",
    38: "Zechariah", 39: "Malachi",
    40: "Matthew", 41: "Mark", 42: "Luke", 43: "John", 44: "Acts",
    45: "Romans", 46: "1 Corinthians", 47: "2 Corinthians", 48: "Galatians",
    49: "Ephesians", 50: "Philippians", 51: "Colossians", 52: "1 Thessalonians",
    53: "2 Thessalonians", 54: "1 Timothy", 55: "2 Timothy", 56: "Titus",
    57: "Philemon", 58: "Hebrews", 59: "James", 60: "1 Peter", 61: "2 Peter",
    62: "1 John", 63: "2 John", 64: "3 John", 65: "Jude", 66: "Revelation"
}

# Topic keywords for common verse topics
TOPIC_KEYWORDS = {
    "love": ["love", "loved", "loveth", "loving", "charity", "beloved"],
    "faith": ["faith", "believe", "believed", "believing", "trust", "faithful"],
    "hope": ["hope", "hoped", "hoping"],
    "peace": ["peace", "peaceable", "peacemakers"],
    "joy": ["joy", "joyful", "rejoice", "rejoicing", "glad", "gladness"],
    "salvation": ["salvation", "saved", "save", "saviour", "redeem", "redeemed"],
    "forgiveness": ["forgive", "forgiven", "forgiveness", "pardon"],
    "grace": ["grace", "gracious"],
    "mercy": ["mercy", "merciful", "mercies"],
    "prayer": ["pray", "prayer", "praying", "prayed"],
    "wisdom": ["wisdom", "wise", "understanding"],
    "strength": ["strength", "strong", "mighty", "power"],
    "comfort": ["comfort", "comforted", "comforter"],
    "healing": ["heal", "healed", "healing", "health"],
    "fear": ["fear", "afraid", "fearful"],
    "sin": ["sin", "sins", "sinner", "sinned", "iniquity"],
    "righteousness": ["righteous", "righteousness"],
    "eternal life": ["eternal", "everlasting", "life"],
    "Holy Spirit": ["spirit", "ghost", "comforter"],
    "Jesus": ["jesus", "christ", "lord", "saviour", "messiah"],
    "God": ["god", "lord", "father", "almighty"],
    "commandment": ["commandment", "commandments", "law"],
    "blessing": ["bless", "blessed", "blessing", "blessings"],
    "heaven": ["heaven", "heavenly", "paradise"],
    "creation": ["created", "creation", "creator", "made"],
    "worship": ["worship", "praise", "glorify", "glory"],
    "truth": ["truth", "true", "faithful"],
    "light": ["light", "lamp", "shine"],
    "shepherd": ["shepherd", "sheep", "lamb", "flock"],
    "resurrection": ["resurrection", "rose", "risen", "raised"],
}


def get_topics(verse_text: str) -> list:
    """Extract relevant topics from verse text."""
    text_lower = verse_text.lower()
    topics = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            topics.append(topic)
    return topics[:5]  # Limit to 5 topics per verse


def download_bible():
    """Download the KJV Bible JSON."""
    print("Downloading KJV Bible from GitHub...")
    
    response = requests.get(BIBLE_URL, timeout=60)
    response.raise_for_status()
    
    # Handle UTF-8 BOM if present
    content = response.content.decode('utf-8-sig')
    return json.loads(content)


def process_bible(bible_data: list) -> list:
    """Process Bible data into our format."""
    verses = []
    
    print("Processing Bible data...")
    
    for book_idx, book_data in enumerate(bible_data):
        # Use 'name' field from JSON, or fall back to our mapping
        book_name = book_data.get("name", BOOK_NAMES.get(book_idx + 1, f"Book {book_idx}"))
        testament = "Old" if book_idx < 39 else "New"
        
        chapters = book_data.get("chapters", [])
        
        for chapter_idx, chapter_verses in enumerate(chapters, 1):
            for verse_idx, verse_text in enumerate(chapter_verses, 1):
                if verse_text.strip():  # Skip empty verses
                    topics = get_topics(verse_text)
                    
                    verses.append({
                        "book": book_name,
                        "chapter": chapter_idx,
                        "verse": verse_idx,
                        "text": verse_text.strip(),
                        "testament": testament,
                        "topic": topics
                    })
    
    return verses


def save_verses(verses: list, output_path: str):
    """Save verses to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(verses, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(verses)} verses to {output_path}")


def main():
    """Main function to download and process Bible."""
    print("=" * 60)
    print("Full KJV Bible Download Script")
    print("=" * 60)
    
    # Setup paths
    data_dir = Path(project_root) / "data" / "bible"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = data_dir / "verses_full.json"
    backup_path = data_dir / "verses_backup.json"
    original_path = data_dir / "verses.json"
    
    # Backup original verses
    if original_path.exists():
        import shutil
        shutil.copy(original_path, backup_path)
        print(f"Backed up original verses to {backup_path}")
    
    try:
        # Download Bible
        bible_data = download_bible()
        print(f"Downloaded {len(bible_data)} books")
        
        # Process into verses
        verses = process_bible(bible_data)
        print(f"Processed {len(verses)} total verses")
        
        # Save full Bible
        save_verses(verses, output_path)
        
        # Also save as main verses.json for the app
        save_verses(verses, original_path)
        
        print("\n" + "=" * 60)
        print("SUCCESS! Full KJV Bible downloaded and processed.")
        print(f"Total verses: {len(verses)}")
        print("=" * 60)
        print("\nNext step: Re-index the database with:")
        print("  python -m app.scripts.reindex_bible")
        
    except requests.RequestException as e:
        print(f"\n✗ Error downloading Bible: {e}")
        print("Please check your internet connection and try again.")
    except Exception as e:
        print(f"\n✗ Error processing Bible: {e}")
        raise


if __name__ == "__main__":
    main()
