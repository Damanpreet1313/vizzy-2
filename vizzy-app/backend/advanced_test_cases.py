import os
import time
import requests

BASE_URL = "http://127.0.0.1:8000"

# Use a timestamp suffix so every test run gets fresh collection names
# and never collides with stale collections left in the DB.
RUN_ID = str(int(time.time()))[-6:]


def setup_test_file(filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename


def teardown_test_file(filename):
    if os.path.exists(filename):
        os.remove(filename)


def run_advanced_tests():
    print("Starting Vizzy Advanced & Edge-Case Testing Suite...\n")

    # =========================================================
    # TEST 1: Block invalid file extensions
    # =========================================================
    print("Test 1: Uploading Invalid File Types (.exe should be blocked)...")
    bad_file = setup_test_file("malicious_script.exe", "exe content")
    with open(bad_file, "rb") as f:
        res = requests.post(f"{BASE_URL}/api/upload",
                            files={"file": (bad_file, f, "application/x-msdownload")})
    assert res.status_code == 400, f"Expected 400, got {res.status_code}: {res.text}"
    print("PASSED - .exe upload correctly blocked with 400.\n")
    teardown_test_file(bad_file)

    # =========================================================
    # TEST 2: Large text / LLM token window protection
    # =========================================================
    print("Test 2: Ingesting large text (3000 words) and running Auto Mode...")
    huge_filename = f"hugebook{RUN_ID}.txt"
    huge_content = "Word " * 3000
    huge_file = setup_test_file(huge_filename, huge_content)

    with open(huge_file, "rb") as f:
        upload_res = requests.post(f"{BASE_URL}/api/upload",
                                   files={"file": (huge_filename, f, "text/plain")},
                                   timeout=60)

    assert upload_res.status_code == 200, f"Upload failed ({upload_res.status_code}): {upload_res.text}"
    upload_data = upload_res.json()
    print(f"  Uploaded: {upload_data['filename']} -> {upload_data['total_chunks']} chunks")

    auto_res = requests.post(f"{BASE_URL}/api/auto-mode",
                             data={"file_path": upload_data["filePath"], "total_frames": 2},
                             timeout=120)
    assert auto_res.status_code == 200, f"Auto-mode failed ({auto_res.status_code}): {auto_res.text}"
    frames = auto_res.json()["collection"]
    assert len(frames) == 2, f"Expected 2 frames, got {len(frames)}"
    print(f"  Auto Mode returned {len(frames)} frames.")
    print(f"  Frame 0 image URL: {frames[0].get('image_url', 'N/A')[:80]}...")
    print("PASSED - Large text handled, LangGraph protected LLM token limits.\n")
    teardown_test_file(huge_file)

    # =========================================================
    # TEST 3: Special characters & unicode
    # =========================================================
    print("Test 3: Uploading file with special characters, unicode & emoji...")
    messy_filename = f"messy{RUN_ID}.txt"
    messy_content = (
        "Chapter 1!!! --- The Dark Cybernetic Nebula... !! @#$%^&*()\n"
        "The protagonist, named XAeA-12, firing hyper-beams!!\n"
        "Newline formatting\r\nis completely broken\there.\n"
        "Unicode: cafe\u0301 na\u00efve \u4e2d\u6587 \u0440\u0443\u0441\u0441\u043a\u0438\u0439"
    )
    messy_file = setup_test_file(messy_filename, messy_content)

    with open(messy_file, "rb") as f:
        upload_res = requests.post(f"{BASE_URL}/api/upload",
                                   files={"file": (messy_filename, f, "text/plain")},
                                   timeout=60)

    assert upload_res.status_code == 200, f"Upload failed ({upload_res.status_code}): {upload_res.text}"
    messy_data = upload_res.json()
    messy_collection = messy_data["collection_name"]
    print(f"  Collection created: '{messy_collection}' with {messy_data['total_chunks']} chunks")
    print("PASSED - Unicode and special characters handled safely.\n")
    teardown_test_file(messy_file)

    # =========================================================
    # TEST 4: Pilot Mode semantic miss (query unrelated to content)
    # =========================================================
    print("Test 4: Pilot Mode semantic miss (query unrelated to document content)...")
    pilot_payload = {
        "user_query": "Explain the recipe for making chocolate chip cookies with sourdough starter.",
        "collection_name": messy_collection,
    }
    pilot_res = requests.post(f"{BASE_URL}/api/pilot-mode", json=pilot_payload, timeout=60)
    assert pilot_res.status_code == 200, f"Pilot mode failed ({pilot_res.status_code}): {pilot_res.text}"

    pilot_data = pilot_res.json()
    assert "reply" in pilot_data, "Missing 'reply' in response"
    assert "imageUrl" in pilot_data, "Missing 'imageUrl' in response"
    print(f"  Vizzy reply: {pilot_data['reply'][:120]}...")
    print(f"  Image URL:   {pilot_data['imageUrl'][:80]}...")
    print("PASSED - Pilot Mode handled semantic miss gracefully.\n")

    print("=" * 60)
    print("All 4 tests passed. Backend is resilient and production-ready.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_advanced_tests()
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend. Make sure uvicorn is running on port 8000.")
