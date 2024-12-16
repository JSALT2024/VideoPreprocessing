import os
import re
import glob
import hashlib
import base64
import cv2
import webvtt
import argparse
import csv
import time
import subprocess
import json
import pandas as pd

def get_file_names(PATH_input):
    video_files = [f for f in os.listdir(PATH_input) if (f.endswith('.mp4') or f.endswith('.webm'))]
    return video_files

def find_matching_files(directory_path, base_filename, fformat, middle_pattern):
    pattern = f"{base_filename}{middle_pattern}{fformat}"
    matching_files = glob.glob(os.path.join(directory_path, pattern))
    return [os.path.basename(f) for f in matching_files]

def get_video_properties(ffmpeg_path,video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video file {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    start = time.time()
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_frames', '-show_entries', 'stream=nb_read_frames', '-of', 'json', "-threads", "16",'-preset', 'ultrafast', video_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    end = time.time()
    print(end-start)
    info = json.loads(result.stdout)
    total_frames = int(info['streams'][0]['nb_read_frames'])

    return fps, width, height, total_frames

def process_clip(ffmpeg_path, video_path, start_time, duration, segment_file):
    command = [
        'ffmpeg', "-ss", str(start_time), "-i", video_path, "-t", str(duration),
        "-c", "copy", segment_file
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Finished processing segment: {segment_file}")

    return segment_file

def trim_video(vtt, video_path, video_id, columns, output_dir, fps, width, height, total_frames, ffmpeg_path="ffmpeg"):
    config_data = []
    for item in columns:
        try:
            columns.remove(',')
        except:
            pass
        try:
            columns.remove('')
        except:
            pass
    columns = [item.split(',') for item in columns if item]

    columns = [[int(item[0]), int(item[1])] for item in columns if len(item) == 2]

    for i, caption in enumerate(vtt.captions):
        try:
            start_frame = columns[i][0]
            end_frame = columns[i][1]
        except IndexError:
            print(f"Skipping segment {i} in {video_id} because no valid timeframes found.")
            continue
        if start_frame < 0:
            print(f"Skipping segment {i} because start frame is out of bounds.")
            continue
        if end_frame > total_frames:
            end_frame = total_frames

        start_time = start_frame / fps
        duration = (end_frame - start_frame) / fps

        segment_file = os.path.join(output_dir, f"{video_id}.{format(start_frame, '06d')}-{format(end_frame, '06d')}.mp4")
        if os.path.exists(segment_file):
            continue
        
        process_clip(ffmpeg_path, video_path, start_time, duration, segment_file)

        ann = re.sub(r'\s+', ' ', caption.text).strip()

        segment_info = {
            "vid_id": video_id,
            "start_frame": start_frame,
            "end_frame": end_frame,
            "annotation": ann,
            "nframes": end_frame - start_frame,
            "fps": round(fps, 2),
            "w": width,
            "h": height,
            "duration": round((end_frame - start_frame) / fps, 2)
        }
        config_data.append(segment_info)
    return config_data

def read_csv_with_variable_columns(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    data = []
    for line in lines:
        parts = line.strip().split('"')
        filename = parts[0][:11]
        columns = parts[0][13:].split(',')
        for part in parts[1:]:
            columns.extend(part.split(','))
        data.append([filename] + columns)
    
    max_columns = max(len(row) for row in data)
    for row in data:
        row.extend([''] * (max_columns - len(row)))
    
    return pd.DataFrame(data)

def main(args):
    data_dir = args.inputdir
    csv_dir = args.csv_dir
    output_dir = args.output
    start_time = time.time()
    os.makedirs(output_dir, exist_ok=True)
    
    file_names = get_file_names(data_dir)
    file_names = [item for item in file_names if "webm.part" not in item]
    ffmpeg_path = args.ffmpeg # Full path to the ffmpeg executable
    all_config_data = []

    try:
        csv_data = read_csv_with_variable_columns(csv_dir)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        exit(1)

    with open(csv_dir, 'r', encoding='utf-8') as csv_file:
        for line in csv_file:
            columns = line[13:].strip().split('"')
            filename = line[:11]

            files_vtts = find_matching_files(data_dir, filename, "vtt", middle_pattern='.*.')
            files_mp4s = find_matching_files(data_dir, filename, "mp4", middle_pattern='.')
            files_webms = find_matching_files(data_dir, filename, "webm", middle_pattern='.')
            files_videos = files_mp4s + files_webms
            if len(files_vtts) == 1:
                vtt_file = files_vtts[0]
            else:
                print(f"No matching VTT file found for {filename}")
                continue
            
            if len(files_videos) == 1:
                video_file = files_videos[0]
            else:
                print(f"No matching video file found for {filename}")
                continue
            
            captions = webvtt.read(os.path.join(data_dir, vtt_file))
            
            video_path = os.path.join(data_dir, video_file)
            
            try:
                fps, width, height, total_frames = get_video_properties(ffmpeg_path, video_path)
            except IOError as e:
                print(e)
                continue
            
            config_data = trim_video(captions, video_path, filename, columns, output_dir, fps, width, height, total_frames, ffmpeg_path)
            
            if config_data:
                all_config_data.extend(config_data)
    
    if all_config_data:
        csv_file = os.path.join(output_dir, "!metadata.csv")
        keys = all_config_data[0].keys()
        with open(csv_file, 'a', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writerows(all_config_data)
    end_time = time.time()

    print(f"Trim in {end_time-start_time}")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process videos with OCR")
    parser.add_argument('--inputdir', type=str, required=True, help="Path to the input files")
    parser.add_argument('--csv_dir', type=str, required=True, help="Output logfile")
    parser.add_argument('--output', type=str, required=True, help="Path to the output video folder")
    parser.add_argument('--ffmpeg', type=str, required=True, help="Path to the ffmpeg executable")
    args = parser.parse_args()
    
    main(args)

