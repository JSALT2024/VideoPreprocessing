import csv

# Define the input file and initialize variables
input_file = 'TRIM/trim_h2s/videos_timestamps/how2sign_realigned_train_frames.csv'
output_file_prefix = 'TRIM/trim_h2s/videos_timestamps/filenames'

# Read the input CSV file
with open(input_file, mode='r', newline='', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    headers = next(reader)  # Read the headers
    rows = list(reader)

# Calculate the number of lines per file
lines_per_file = len(rows) // 10

# Function to write a chunk of rows to a new CSV file
def write_chunk(file_index, chunk):
    output_file = f"{output_file_prefix}{file_index + 1}.csv"
    with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(headers)
        writer.writerows(chunk)

# Iterate and save each chunk into a new file
for i in range(10):
    start_index = i * lines_per_file
    end_index = (i + 1) * lines_per_file if i < 9 else len(rows)
    chunk = rows[start_index:end_index]
    write_chunk(i, chunk)

print("CSV file has been successfully divided into 10 parts.")
