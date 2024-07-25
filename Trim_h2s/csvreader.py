import itertools

csv_dir = 'TRIM/trim_h2s/videos_timestamps/how2sign_realigned_test_frames.csv'

with open(csv_dir, 'r', encoding='utf-8') as csv_file:
    lines = csv_file.readlines()

# Pairing the lines two at a time
paired_lines = itertools.zip_longest(*[iter(lines)]*2)

for line1, line2 in paired_lines:
    # Processing the first line
    columns1 = line1.split('"')[1:]
    filename1 = line1.split(',')[0]
    print(f"Filename1: {filename1}")
    print(f"Columns1: {columns1}")

    # Processing the second line
    if line2:
        columns2 = line2.split('"')[1:]
        filename2 = line2.split(',')[0]
        print(f"Filename2: {filename2}")
        print(f"Columns2: {columns2}")
