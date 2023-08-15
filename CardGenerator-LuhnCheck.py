def luhn_check(number):
    digits = [int(digit) for digit in number]
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    total = sum(digits)
    return total % 10 == 0

def main():
    unchanged_prefix = "123456"  # Replace with your actual unchanged prefix
    unchanged_suffix = "7890"    # Replace with your actual unchanged suffix

    start_count = 0
    end_count = 999999

    with open("numbers.txt", "w") as output_file:
        for count in range(start_count, end_count + 1):
            middle_part = str(count).zfill(6)
            final_number = unchanged_prefix + middle_part + unchanged_suffix

            if luhn_check(final_number):
                output = final_number + " - Passed Luhn algorithm check\n"
            else:
                output = final_number + " - Failed Luhn algorithm check\n"

            print(output, end="")
            output_file.write(output)

if __name__ == "__main__":
    main()
