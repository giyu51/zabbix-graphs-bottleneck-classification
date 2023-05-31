
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from matplotlib import pyplot as plt
import datetime
import json


# Customization

with open("zabbix_conf.json", 'r') as conf_file:
    conf_file = json.load(conf_file)
    training_conf = conf_file['Model Training']
    
# Set the path to the main directory containing the training and testing folders
main_dir =training_conf['main_dir']

# Define the subdirectories
train_dir =training_conf['train_dir']
test_dir =training_conf['test_dir']
logs_dir =training_conf['logs_dir']

# Set the desired image settings
image_width =training_conf['image_width']
image_height =training_conf['image_height']
image_size = (image_width, image_height)
resize_factor =training_conf['resize_factor']
batch_size =training_conf['batch_size']

# Specify the exact names of the two classes (two directories) located in both subdirectories
class_names =training_conf['class_names']
epochs = training_conf['epochs']



print('_________________________________________________________')
print(f'Main directory is set to {main_dir}')
print(f'Training subdirectory is set to {train_dir}')
print(f'Testing subdirectory is set to {test_dir}')
print('_________________________________________________________')
print(f'Image width: {image_width}')
print(f'Image height: {image_height}')
print(f'Image will be resized to {resize_factor*100}% of its original size')
print('_________________________________________________________')
print(f'Batch size: {batch_size}')
print(f'Number of training cycles (epochs): {epochs}')
print('_________________________________________________________')






# Create the training dataset
train_dataset = tf.keras.preprocessing.image_dataset_from_directory(
    directory=train_dir,
    labels='inferred',
    label_mode='binary',
    color_mode='rgb',
    class_names=class_names,
    batch_size=batch_size,
    image_size=image_size,
    shuffle=True
)

# Create the testing dataset
test_dataset = tf.keras.preprocessing.image_dataset_from_directory(
    directory=test_dir,
    labels='inferred',
    label_mode='binary',
    color_mode='rgb',
    class_names=class_names,
    batch_size=batch_size,
    image_size=image_size,
    shuffle=False
)




# Apply a function to the datasets using the map() method
# Normalize pixel values to [0, 1]
train_dataset = train_dataset.map(lambda x, y: (x / 255.0, y))
test_dataset = test_dataset.map(lambda x, y: (x / 255.0, y))


reduced_image_size = (int(image_size[0] * resize_factor), int(image_size[1] * resize_factor))

# Resize images in the datasets
train_dataset = train_dataset.map(lambda x, y: (tf.image.resize(x, reduced_image_size), y))
test_dataset = test_dataset.map(lambda x, y: (tf.image.resize(x, reduced_image_size), y))



model = Sequential()
model.add(Conv2D(32, (3, 3), activation='relu', input_shape=(reduced_image_size[0], reduced_image_size[1], 3)))
model.add(MaxPooling2D((2, 2)))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D((2, 2)))
model.add(Conv2D(128, (3, 3), activation='relu'))
model.add(MaxPooling2D((2, 2)))
model.add(Flatten())
model.add(Dense(128, activation='relu'))
model.add(Dense(1, activation='sigmoid'))



model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])



history = model.fit(train_dataset, epochs=epochs, batch_size=batch_size)


# Evaluate the model on the test dataset
testing_loss, testing_accuracy = model.evaluate(test_dataset)

print(f'Test Loss: {testing_loss}, Test Accuracy: {testing_accuracy}')



# Access the accuracy and loss values from the history object
training_accuracy = history.history['accuracy']
training_loss = history.history['loss']

# Create subplots for accuracy and loss
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))

# Plot accuracy
ax1.plot(range(1, len(training_accuracy) + 1), training_accuracy, label='Training Accuracy')
ax1.set_xlabel('Epoch')
ax1.set_ylabel('Accuracy')
ax1.set_title('Training Accuracy')
ax1.legend()

# Plot loss
ax2.plot(range(1, len(training_loss) + 1), training_loss, label='Training Loss')
ax2.set_xlabel('Epoch')
ax2.set_ylabel('Loss')
ax2.set_title('Training Loss')
ax2.legend()

plt.tight_layout()

# Save the figure
plt.savefig(f'{logs_dir}/training_plot.png')



logs = {
    "Time": {
        "date":datetime.datetime.now().strftime('%D'),
        "time":datetime.datetime.now().strftime('%T')
    },
    
    "DIR-Config": {
        "Main DIR": main_dir,
        "Training SUB-DIR": train_dir,
        "Testing SUB-DIR": test_dir
    },
    
    "Image-Config": {
        "Image width":image_width,
        "Image height":image_height,
        "Image resize":resize_factor
    },
    
    "Training Config": {
        "Batch size": batch_size,
        "Epochs": epochs,
    },
    
    "MODEL OUT": {
      "Training Loss":training_loss[-1],
      "Training Accuracy":training_accuracy[-1],
      "Training Progress": [f"Epoch {epoch+1}: Accuracy = {training_accuracy[epoch]}, Loss = {training_loss[epoch]}" for epoch in range(len(training_accuracy))],

      "Testing Loss":testing_loss,
      "Testing Accuracy": testing_accuracy,

    }
    
}

# Write the data to json file
with open(f"{logs_dir}/zabbix_logs.json", "a") as json_file:
    json.dump(logs, json_file)


# Save model
model.save('./MK-1')


