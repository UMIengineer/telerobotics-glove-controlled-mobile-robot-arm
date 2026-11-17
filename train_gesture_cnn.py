import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
from sklearn.metrics import confusion_matrix, classification_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(BASE_DIR, "hand_gesture_dataset_processed_10")

train_data = tf.keras.utils.image_dataset_from_directory(
    os.path.join(dataset_path, "train"),
    image_size=(50, 50),
    batch_size=32,
    color_mode="grayscale",
    label_mode="categorical",
    shuffle=True,
)

val_data = tf.keras.utils.image_dataset_from_directory(
    os.path.join(dataset_path, "val"),
    image_size=(50, 50),
    batch_size=32,
    color_mode="grayscale",
    label_mode="categorical",
    shuffle=False,
)

test_data = tf.keras.utils.image_dataset_from_directory(
    os.path.join(dataset_path, "test"),
    image_size=(50, 50),
    batch_size=32,
    color_mode="grayscale",
    label_mode="categorical",
    shuffle=False,
)

class_names = train_data.class_names
num_classes = len(class_names)

with open(os.path.join(BASE_DIR, "class_indices_v4.json"), "w") as f:
    json.dump(class_names, f)

model = models.Sequential([
    layers.Rescaling(1.0 / 255, input_shape=(50, 50, 1)),
    layers.Conv2D(16, 3, padding="same", activation="relu"),
    layers.MaxPooling2D(),
    layers.Conv2D(32, 3, padding="same", activation="relu"),
    layers.MaxPooling2D(),
    layers.Conv2D(64, 3, padding="same", activation="relu"),
    layers.Flatten(),
    layers.Dropout(0.2),
    layers.Dense(128, activation="relu"),
    layers.Dense(num_classes, activation="softmax"),
])

model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"],
)

checkpoint = ModelCheckpoint(
    os.path.join(BASE_DIR, "hand_gesture_model_best.keras"),
    monitor="val_loss",
    save_best_only=True,
    verbose=1,
)
earlystop = EarlyStopping(
    monitor="val_loss",
    patience=5,
    restore_best_weights=True,
    verbose=1,
)

model.fit(
    train_data,
    validation_data=val_data,
    epochs=30,
    callbacks=[checkpoint, earlystop],
    verbose=1,
)

test_loss, test_accuracy = model.evaluate(test_data)
print(f"Test Loss: {test_loss:.4f} | Test Accuracy: {test_accuracy:.4f}")

y_true = np.concatenate([np.argmax(y.numpy(), axis=1) for _, y in test_data], axis=0)
y_pred = np.argmax(model.predict(test_data, verbose=1), axis=1)
print("\nConfusion Matrix:\n", confusion_matrix(y_true, y_pred))
print("\nClassification Report:\n", classification_report(y_true, y_pred, target_names=class_names))

# Export to FP16 TensorFlow Lite for Raspberry Pi 4B deployment
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_types = [tf.float16]
tflite_model = converter.convert()

with open(os.path.join(BASE_DIR, "model_12.tflite"), "wb") as f:
    f.write(tflite_model)
