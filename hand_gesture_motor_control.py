import cv2
import numpy as np
import json
import mediapipe as mp

try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    import tensorflow as tf
    Interpreter = tf.lite.Interpreter


class RobotVision:
    def __init__(
        self,
        model_path="model_12.tflite",
        labels_path="class_indices_v4.json",
    ):
        with open(labels_path, "r") as json_file:
            self.labels = json.load(json_file)

        self.interpreter = Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def get_gesture(self, show_debug=True):
        """Capture one frame and return (gesture_label, confidence)."""
        ret, frame = self.cap.read()
        if not ret:
            return "camera error", 0.0

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)

        gesture_text = "none"
        confidence = 0.0

        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                cx = int(hand_lms.landmark[9].x * w)
                cy = int(hand_lms.landmark[9].y * h)

                box = 400
                x1, y1 = max(0, cx - box // 2), max(0, cy - box // 2)
                x2, y2 = min(w, x1 + box), min(h, y1 + box)
                roi = frame[y1:y2, x1:x2]

                if roi.size > 0:
                    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                    img_resized = cv2.resize(gray_roi, (50, 50))
                    img_final = img_resized.astype(np.float32).reshape(1, 50, 50, 1)

                    self.interpreter.set_tensor(self.input_details[0]["index"], img_final)
                    self.interpreter.invoke()

                    predictions = self.interpreter.get_tensor(self.output_details[0]["index"])
                    class_idx = int(np.argmax(predictions[0]))
                    confidence = float(predictions[0][class_idx])

                    try:
                        gesture_text = self.labels[class_idx]
                    except IndexError:
                        gesture_text = "unknown"

                    if show_debug:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.imshow("Model Insight", cv2.resize(img_resized, (200, 200)))

        if show_debug:
            cv2.putText(
                frame,
                f"Signal: {gesture_text} ({confidence:.1%})",
                (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
            cv2.imshow("Robot Feed", frame)
            cv2.waitKey(1)

        return gesture_text, confidence

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()
