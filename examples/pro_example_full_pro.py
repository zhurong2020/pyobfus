def _check_debugger():
    import sys
    if sys.gettrace() is not None:
        sys.exit(1)
_ENCRYPTION_KEY = b'X9oP2EFWjxAK7OUL97ppm5MbNgQDMlR9oxNiskb77pM='

def _decrypt_str(encrypted_b64):
    from cryptography.fernet import Fernet  # type: ignore[import-not-found]
    import base64
    cipher = Fernet(_ENCRYPTION_KEY)
    encrypted_bytes = base64.b64decode(encrypted_b64)
    return cipher.decrypt(encrypted_bytes).decode('utf-8')
'\nExample for testing Pro features (AES encryption + anti-debugging).\n\nThis file demonstrates cardiac-ml-research style code with\nsensitive strings that should be encrypted in Pro version.\n'

def I3(I15, I5):
    _check_debugger()
    I1 = _decrypt_str(b'Z0FBQUFBQnBFME54SlA1YWxZRjk3Mnd4ZUhCLXB4SVF1WGpqV0doV3V1QjJvMGZkS2ZMTHdFdTU3OU02SWhpNXZYVU1BbzRuYlRxdldubGVoUXBWYWo4X1poellmMy0zelVab3RTaDBTSk56YUxKOGdxcmRyLVk9')
    I14 = _decrypt_str(b'Z0FBQUFBQnBFME54bi1BVXFvMDZ4eG1uODNkaHhDOURTaFpFNERmbFkzQ3Q0MDlROGdyQjktd2ZDMTVZZ0F1T2IwVnpFT3RUNkRGc2pyM09LN054b3NSbkdlZDBKaHl3S3c9PQ==')
    I0 = 0.4
    if I5 > 200:
        I8 = 4
        I4 = _decrypt_str(b'Z0FBQUFBQnBFME54SGs3SVVkZGZ0N1JZU3U2NXgteFNsZTRZNkRNSGlXX3JmOWZlX1VxSWVtamNIMUFCd2k5X0ZVQnk1QmxjY1I4dVgzd1V0V2tCbXRrVmRSeEowVDFhbmc9PQ==')
    elif I5 > 130:
        I8 = 3
        I4 = _decrypt_str(b'Z0FBQUFBQnBFME54bGkyZnNhLUNrcGxjVTVZNUtHUVJUR1pxdGd5RGRfM2E5ekpocy1GMTRZMUQ1QXRzbmtSc1lHMEhQVm9WWU4yc2xkb093aUFjd29zY2M0VkRrUUVsUlE9PQ==')
    elif I5 > 70:
        I8 = 2
        I4 = _decrypt_str(b'Z0FBQUFBQnBFME54MkJtSnhOTmFuc0E5SGhsTjMxamIyX0dMY0tzeUtBSWF6TW40NmtKNnM5aVJSc2xDc1ZhVHY3ODhKSTdBSHlsRTNibkgtdDhIbElUaGtxMVUxVHYyaHc9PQ==')
    else:
        I8 = 1
        I4 = _decrypt_str(b'Z0FBQUFBQnBFME54QTVGR2Z5ZFNlVXVLSjVhQzdXM1Q3Q1FtdWE3NXh1RjFXRGVBQVRwYTNnMlJYM0RlM3ZwcklFZmI4UFV4bmhyNmoxcE9Rc19uSUZYT1Y4aUQ0R3F4eVE9PQ==')
    I11 = I15 * I8 * I0
    I6 = f'Algorithm: {I1} {I14}'
    I10 = f'Patient calcium score: {I11:.2f} ({I4})'
    print(I6)
    print(I10)
    return I11

def main():
    _check_debugger()
    I13 = 50.0
    I12 = 150.0
    I2 = 'MEDICAL_API_KEY_12345'
    I7 = _decrypt_str(b'Z0FBQUFBQnBFME54U1lpVjZZMlE4Uk42V2JWclg0bTR5Vy1PT1BkNEJVYUFkRmQ2VkZ6OWJfM0JpV2NBUnJsVFNhdWhlTkJjWmJIVlplNTd0X0FWaUN4SnZhbGJjcXZLNERpOHJ1NHh2WldqOHRmN0Q1bzI0dzc2YnFIWmlaUkE3UGZObWNCMHdlZzY=')
    print(_decrypt_str(b'Z0FBQUFBQnBFME54Skgyd09mNDNLaUpwRUpJMU55TERNM0dkU2Fxai1iMmtaTVJKdi1zOE5ZRXBUc2NsOXh4TnpNN0lwYmZWSU05TUxtdG81WGJBNjBXMFpLcjJGSERpT1JLaUF5SFRMa1puaUxGcGE2MTZvN010dWhFT0EtbkRfRm5yYVZUYXJPNVI='))
    print(f'API Key: {I2}')
    print(f'Model Path: {I7}')
    print()
    I11 = I3(I13, I12)
    if I11 > 100:
        I9 = _decrypt_str(b'Z0FBQUFBQnBFME54Tkk4UEFDQUI2VURoOFd4YkN2TXkydFlXektzdkFsUDVSU0RDc1dsRHNGalpyRjVuNXNxZmFJWmRmZkdrS2xlc1FDT3A1a3kzenpubXM3YW9tNDBoQkJvVzhTNXFsQzVuSVRpSFE1ZzU0UUZnR3RnUU9PblVucE9qTHFoZ1VDOWg=')
    else:
        I9 = _decrypt_str(b'Z0FBQUFBQnBFME54QkVkbVdVTVpybjFWRS04Ynd1dEdLSzU5VURMNWpJWXRtdzl3Ni15TzJwN21HWkdUa1JwSGo5Y1JLTHF4blhMbU5vQ3E0eTk3UnRzU0hhSHEtLV93UE9IQ2dpRGRBcnBXODFzOWg0NTFlMjA9')
    print()
    print(f'Clinical Recommendation: {I9}')
if __name__ == '__main__':
    main()