import cv2
import pytesseract

def extract_text_from_frame(frame):
    return pytesseract.image_to_string(frame)

cap = cv2.VideoCapture('C:/Users/valac/OneDrive - Západočeská univerzita v Plzni/JHU/work/transcribe_by_ocr/video.mp4')
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    text = extract_text_from_frame(frame)
    print(text)

cap.release()
cv2.destroyAllWindows()
