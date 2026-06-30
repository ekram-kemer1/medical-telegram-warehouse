import os
import csv
import logging
from pathlib import Path
from ultralytics import YOLO

BASE_DIR    = Path(__file__).resolve().parent.parent
IMAGES_DIR  = BASE_DIR / "data" / "raw" / "images"
OUTPUT_CSV  = BASE_DIR / "data" / "yolo_detections.csv"
LOGS_DIR    = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "yolo_detect.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

log.info("Loading YOLOv8n model...")
model = YOLO("yolov8n.pt")


def classify_image(detected_classes):
    has_person = "person" in detected_classes
    product_objs = {"bottle", "cup", "bowl", "vase", "wine glass", "box"}
    has_product = bool(set(detected_classes) & product_objs)

    if has_person and has_product:
        return "promotional"
    elif has_product and not has_person:
        return "product_display"
    elif has_person and not has_product:
        return "lifestyle"
    else:
        return "other"


def run_detection():
    rows = []
    image_files = list(IMAGES_DIR.glob("**/*.jpg"))
    log.info(f"Found {len(image_files)} images to process")

    for img_path in image_files:
        channel_name = img_path.parent.name
        message_id   = img_path.stem

        try:
            results = model(str(img_path), verbose=False)
            result  = results[0]

            detected_classes = []
            confidences = []

            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf   = float(box.conf[0])
                cls_name = model.names[cls_id]
                detected_classes.append(cls_name)
                confidences.append(conf)

            category = classify_image(detected_classes)

            if detected_classes:
                for cls_name, conf in zip(detected_classes, confidences):
                    rows.append({
                        "channel_name":     channel_name,
                        "message_id":       message_id,
                        "image_path":       str(img_path),
                        "detected_class":   cls_name,
                        "confidence_score": round(conf, 4),
                        "image_category":   category,
                    })
            else:
                rows.append({
                    "channel_name":     channel_name,
                    "message_id":       message_id,
                    "image_path":       str(img_path),
                    "detected_class":   "none",
                    "confidence_score": 0.0,
                    "image_category":   "other",
                })

            log.info(f"{img_path.name}: {category} ({len(detected_classes)} objects)")

        except Exception as e:
            log.error(f"Failed to process {img_path}: {e}")

    if rows:
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        log.info(f"DONE: {len(rows)} detection records saved to {OUTPUT_CSV}")
    else:
        log.warning("No images found to process")


if __name__ == "__main__":
    run_detection()