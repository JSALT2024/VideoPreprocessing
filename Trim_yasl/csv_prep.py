import csv
import argparse

def process_tsv(file_path):
    frames = {}

    # Read the .tsv file and extract start and end frames for each ID
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                columns = line.strip().split('\t')
                id_col = columns[2]
                start_frame = int(columns[3])
                end_frame = int(columns[4])

                if id_col not in frames:
                    frames[id_col] = []

                frames[id_col].append((start_frame, end_frame))

    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as file:
            for line in file:
                columns = line.strip().split('\t')
                id_col = columns[2]
                start_frame = int(columns[3])
                end_frame = int(columns[4])

                if id_col not in frames:
                    frames[id_col] = []

                frames[id_col].append((start_frame, end_frame))

    return frames

def create_csv_from_frames(frames, output_csv_path):
    with open(output_csv_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)

        for id_col, frame_list in frames.items():
            row = [id_col] + [f"{start},{end}" for start, end in frame_list]
            csvwriter.writerow(row)

def main(args):
    tsv_file_path = args.input_tsv
    output_csv_path = args.output_csv

    frames = process_tsv(tsv_file_path)
    create_csv_from_frames(frames, output_csv_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a TSV file and generate a CSV output.")
    parser.add_argument('--input_tsv', type=str, required=True, help="Path to the input .tsv file")
    parser.add_argument('--output_csv', type=str, required=True, help="Path to the output .csv file")
    args = parser.parse_args()

    main(args)
