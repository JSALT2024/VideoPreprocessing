import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import cv2
import easyocr
import csv
from time import time

# Initialize EasyOCR reader globally to share among processes
reader = easyocr.Reader(['en'])

# Function to perform OCR on the lower 30% of an image within x-axis range [500, 1500]
def perform_ocr_on_frame(frame):
    height, width, _ = frame.shape
    lower_30_height = int(height * 0.3)
    x_start = 500
    x_end = 1500 if width > 1500 else width
    cropped_frame = frame[height - lower_30_height:height, x_start:x_end]
    ocr_result = reader.readtext(cropped_frame, detail=0)
    return ' '.join(ocr_result).strip()

# Function to process video and get OCR results for each frame
def process_video(video_path, csv_path):
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    previous_ocr_text = ""
    current_range_start = 0

    # Ensure the directory for the CSV file exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    start_time = time()
    print(f"Processing {frame_count} frames from video...")

    with open(csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['start_frame', 'end_frame', 'ocr_text'])
        file.flush()  # Ensure header is written immediately

        for i in range(frame_count):
            print(f"Processing frame {i + 1}/{frame_count}")
            ret, frame = cap.read()
            if not ret:
                break

            ocr_text = perform_ocr_on_frame(frame)
            print(f"Frame {i}: OCR Text - '{ocr_text}'")

            if ocr_text != previous_ocr_text:
                if previous_ocr_text:
                    writer.writerow([current_range_start, i - 1, previous_ocr_text])
                    print(f"Wrote row: [{current_range_start}, {i - 1}, '{previous_ocr_text}']")
                    file.flush()  # Ensure data is written immediately
                previous_ocr_text = ocr_text
                current_range_start = i

            if (i + 1) % 100 == 0 or (i + 1) == frame_count:
                print(f"Processed {i + 1}/{frame_count} frames")

        # Add the last range
        if previous_ocr_text:
            writer.writerow([current_range_start, frame_count - 1, previous_ocr_text])
            print(f"Wrote final row: [{current_range_start}, {frame_count - 1}, '{previous_ocr_text}']")
            file.flush()  # Ensure final data is written

    cap.release()

    end_time = time()
    print(f"Total time taken: {end_time - start_time:.2f} seconds")

# Define paths
video_path = 'C:/Users/valac/OneDrive - Západočeská univerzita v Plzni/JHU/work/transcribe_by_ocr/video.mp4'
csv_path = 'C:/Users/valac/OneDrive - Západočeská univerzita v Plzni/JHU/work/transcribe_by_ocr/annotations_ocr.csv'

# Run the main process
process_video(video_path, csv_path)
