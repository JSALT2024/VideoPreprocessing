import csv

def process_tsv(file_path):
    frames = {}
    
    # Read the .tsv file and extract start and end frames for each ID
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                columns = line.strip().split('\t')
                id_col = columns[1]
                clip_name = columns[3]
                start_frame = columns[4]
                end_frame = columns[5]
                
                if id_col not in frames:
                    frames[id_col] = []
                key = f"{id_col}_clips"
                if key not in frames:
                    frames[key] = []
                
                frames[id_col].append((start_frame, end_frame))
                
                frames[key].append(clip_name)
    
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as file:
            for line in file:
                columns = line.strip().split('\t')
                id_col = columns[1]
                start_frame = columns[5]
                end_frame = columns[6]
                
                if id_col not in frames:
                    frames[id_col] = []
                
                frames[id_col].append((start_frame, end_frame))
    
    return frames

def create_csv_from_frames(frames, output_csv_path):
    with open(output_csv_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        
        for id_col, frame_list in frames.items():
            try:
                row = [id_col] + [f"{start},{end}" for start, end in frame_list]
                csvwriter.writerow(row)
            except:
                row = [id_col] + [f"{cli}" for cli in frame_list]
                csvwriter.writerow(row)

def main(tsv_file_path, output_csv_path):
    frames = process_tsv(tsv_file_path)
    create_csv_from_frames(frames, output_csv_path)

# Replace with the path to your .tsv file and the output CSV file path
tsv_file_path = "TRIM/trim_h2s/videos_timestamps/how2sign_realigned_train.csv"
output_csv_path = 'TRIM/trim_h2s/videos_timestamps/how2sign_realigned_train_frames.csv'
main(tsv_file_path, output_csv_path)
