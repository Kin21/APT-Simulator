import random


def compute_crc32k(input_sequence):
    
    polynomial = 0x32583499
    
    crc = 0xFFFFFFFF
    
    for bit in input_sequence:
        
        crc ^= (bit << 31)
        
        for _ in range(32):
            if crc & 0x80000000:
                crc = (crc << 1) ^ polynomial
            else:
                crc = crc << 1
            
            crc &= 0xFFFFFFFF
    
    return crc


def generate_random_sequence(length):
    
    return [random.randint(0, 1) for _ in range(length)]


def verify_crc_functions():
    
    sequence = generate_random_sequence(1000)
    
    crc = compute_crc32k(sequence)
    
    extended_sequence = sequence + [int(bit) for bit in format(crc, '032b')]
    
    verification_crc = compute_crc32k(extended_sequence)
    
    return verification_crc == 0


if __name__ == "__main__":
    
    is_valid = verify_crc_functions()
    
    print("CRC Verification:", "Passed" if is_valid else "Failed")
