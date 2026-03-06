import sys
import jwt

def inspect_token(token):
    try:
        header = jwt.get_unverified_header(token)
        print("HEADER:", header)
        payload = jwt.decode(token, options={"verify_signature": False})
        print("PAYLOAD:", payload)
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect_token(sys.argv[1])
    else:
        print("Please provide a token")
