import sys
import pyAesCrypt


def decrypt_file(input_file, output_file, password):
    try:
        pyAesCrypt.decryptFile(input_file, output_file, password)
        print(f"Decryption successful: {output_file}")
    except Exception as e:
        print(f"Decryption failed: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python decrypt.py <input_file> <output_file> <password>")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    password = sys.argv[3]

    decrypt_file(input_file, output_file, password)
