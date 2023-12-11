from asyncio.windows_events import NULL
from PIL import ImageTk, Image
import cv2
import os
import numpy as np
from tkinter import simpledialog
from tkinter import messagebox


class program:
    def __init__(self):
        # Initialize class variables

        # self.video_name = "20020924_juve_dk_02a.mpg"
        # self.video_name = "20020924_juve_dk_02a.avi"
        self.video_name = r".\\20020924_juve_dk_02a_1.avi"
        self.resolution = 0
        self.frame_width = 352
        self.frame_height = 288
        self.start_frame = 1000
        self.end_frame = 4999

        # Lists to store PIL images, standard deviations, and averages
        self.pil_imgs = []
        self.column_stds = []
        self.column_avgs = []

        # Numpy array to store intensity bins
        self.intensity_bins = np.array([])
        
        # Lists and variables for storing results and thresholds
        self.sd_array = []
        self.tb = 0
        self.ts = 0
        self.tor = 2
        self.frame_results = {"cs" : [], "ce" : [],
                             "fs" : [], "fe" : []}
        
        # List to store frame images
        self.frame_images = []
    
    # Prompt user to load or generate intensity bins
    def get_intensity_bins(self):
        # Ask the user whether to load pre-existing intensity bins
        response = messagebox.askquestion("Load pre-existing intensity bins?", "Load pre-existing intensity bins?", icon='question')
        # Check the user's response
        if response.lower() == "no":
            # If the user chooses not to load, generate new intensity bins
            self.generate_intensity_bins()
        # If the user chooses to load, load intensity bins from a file
        elif response.lower() == "yes":
                self.intensity_bins = self.load_intensity_bins()
                # Convert intensity_bins to list format
                self.intensity_bins = np.array(self.intensity_bins).tolist()
        
    # Load intensity bins from a file
    def load_intensity_bins(self):
        return self.read_file("intensity_bins")
    
    # Get dimensions of the video frames
    def get_dimensions(self):
        # Open the video file for capturing frames
        video_capture = cv2.VideoCapture(self.video_name)
        # Read the first frame from the video
        success, image = video_capture.read()
        
        # Set the instance variables to the width, height, and resolution of the first frame
        self.frame_width = image.shape[1]
        self.frame_height = image.shape[0] 
        self.resolution = self.frame_width * self.frame_height
        
    # Extract frames from the video
    def extract_frames(self):
        print("Extracting frames...")
        # Open the video file for capturing frames
        video_capture = cv2.VideoCapture(self.video_name)
        # Read the first frame from the video to get dimensions
        success, image = video_capture.read()
        
        # Set the initial values for frame width, height, and resolution
        self.frame_width = image.shape[1]
        self.frame_height = image.shape[0] 
        self.resolution = self.frame_width * self.frame_height
        
        count = 0 
        
        # Create a directory to store the extracted frames
        dirname = os.path.dirname(__file__)
        # path = os.path.join(dirname, 'frame_images')
        path= r".\\frame_images"
        
        while success:
            # Skip frames until the start_frame is reached
            while count < self.start_frame:
                success,image = video_capture.read()
                count += 1
            # Save frames within the specified range
            if (count <= self.end_frame):
                filepath = os.path.join(path, "frame%d.jpg" % count)
                cv2.imwrite(filepath, image) 
                
                # Open the saved image and store it in the pil_imgs list
                img = Image.open(filepath)
                self.pil_imgs.append(img)
                
                success,image = video_capture.read()
                count += 1
                continue
            break

        print(f'{self.end_frame - self.start_frame + 1} frames have been read')

    # Calculate intensity histogram for a given RGB frame
    def calculate_intensity(self, rgb_frame):
        intensity_values = np.dot(rgb_frame[..., :3], [0.299, 0.587, 0.114])
        return np.histogram(intensity_values, bins = np.arange(0,256,10))[0]

    # Generate intensity bins for the video frames
    def generate_intensity_bins(self):
        
        # Open the video file for capturing frames
        video_capture_frame = cv2.VideoCapture(self.video_name)
        
        # Check if the video file is opened successfully
        if not video_capture_frame.isOpened():
            print("Error: Could not open video file.")
            return None  

        # Specify the range of frames to process
        frames_to_process = range(1000, 5000)
        # Get the total number of frames in the video
        total_frames = int(video_capture_frame.get(cv2.CAP_PROP_FRAME_COUNT))
        print("Total frames in the video:", total_frames)

        # List to store intensity histograms for each processed frame
        intensity_histograms = []

        # Loop through all frames in the video
        for frame_index in range(total_frames):
            # Read the next frame from the video
            result, frame = video_capture_frame.read()
            # Check if the frame is successfully read
            if not result:
                break

            # Process frames within the specified range
            if frame_index in frames_to_process:
                # Convert the frame to RGB format
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Calculate intensity histogram using the calculate_intensity method
                intensity_histogram = self.calculate_intensity(rgb_frame)
                # Append the calculated histogram to the list
                intensity_histograms.append(intensity_histogram)

        # Release the video capture object
        video_capture_frame.release()
        # Convert the list of intensity histograms to a NumPy array
        self.intensity_bins = np.array(intensity_histograms)

        # Save the intensity bins to a file
        self.save_file(self.intensity_bins, "intensity_bins")

        return self.intensity_bins

    # Save data to a file
    def save_file(self, data, file_name):
        try:
            file = open(file_name, "wb") 
            np.save(file, data) 
            
        except Exception:
            print("Something went wrong: " + str(Exception))
        
        finally:
            file.close
    
    # Read data from a file
    def read_file(self, file_name):
        data = None
        
        try:
            file = open(file_name, "rb") 
            data = np.load(file) 
            
        except Exception:
            print("Something went wrong: " + str(Exception))
            
        finally:
            file.close
            return data

    # Generate standard deviations for intensity bins
    def get_sd(self):
        # Loop through intensity bins, excluding the last one
        for i in range(len(self.intensity_bins) - 1):
            # Get intensity bins for two consecutive frames
            first_bin = self.intensity_bins[i]
            second_bin = self.intensity_bins[i + 1]
            # Initialize total standard deviation for the current pair of frames
            sd_total = 0
            # Loop through bins (histogram bins)
            for j in range(25):
                # Calculate absolute difference between corresponding bins
                difference = abs(first_bin[j] - second_bin[j])
                # Accumulate the differences to calculate total standard deviation
                sd_total += difference
            # Append the total standard deviation for the current pair of frames to sd_array
            self.sd_array.append(sd_total)


    # Set thresholds based on standard deviations
    def apply_threshold(self):
        # Convert sd_array to NumPy array with data type int32
        self.sd_array = np.asarray(self.sd_array, dtype=np.int32)
        
        # Calculate shot cut threshold (Ts)
        self.ts = np.mean(self.sd_array) * 2
        print("Ts = ",self.ts)
        
        # Calculate gradual transition threshold (Tb)
        self.tb = np.mean(self.sd_array) + np.std(self.sd_array) * 11
        print("Tb = ",self.tb)
        
        
    # Find cuts and gradual transitions in the video frames
    def get_frames(self):
        cs = 0  # Variable to store the start frame index of a shot cut
        ce = 0  # Variable to store the end frame index of a shot cut

        fs = 0  # Variable to store the start frame index of a gradual transition
        fe = 0  # Variable to store the end frame index of a gradual transition
        tor = 0  # Temporary variable to track the number of frames below Ts during a gradual transition

        fs_candi = 0  # Candidate variable for the start frame index of a gradual transition
        fe_candi = 0  # Candidate variable for the end frame index of a gradual transition

        skip_to_frame = 0  # Variable to skip frames already processed to avoid redundant checks

        # Loop through the standard deviation array
        for frame_ind in range(len(self.sd_array)):
            # Skip frames already processed
            if frame_ind <= skip_to_frame:
                continue

            # Check if the current frame's standard deviation is above the gradual transition threshold (Tb)
            if self.sd_array[frame_ind] >= self.tb:
                cs = frame_ind
                ce = frame_ind + 1

                # Add shot cut frames to the results dictionary
                self.frame_results["cs"].append(cs + self.start_frame)
                self.frame_results["ce"].append(ce + self.start_frame)

                skip_to_frame = ce  # Skip frames already identified as a shot cut

            # Check if the current frame's standard deviation is between shot cut threshold (Ts) and Tb
            elif self.ts <= self.sd_array[frame_ind] < self.tb:
                fs_candi = frame_ind

                # Loop through frames after the current frame
                for after_frame_ind in range(frame_ind + 1, len(self.sd_array)):
                    # Check if the standard deviation is between Ts and Tb
                    if self.ts <= self.sd_array[after_frame_ind] < self.tb:
                        tor = 0  # Reset the temporary variable if standard deviation is within the range
                        continue
                    # Check if the standard deviation is below Ts
                    elif self.sd_array[after_frame_ind] < self.ts:
                        tor += 1  # Increment the temporary variable
                        # Check if three consecutive frames are below Ts
                        if tor == 2:
                            fe_candi = after_frame_ind - 2
                            # Process the gradual transition frames
                            self.summation(fs_candi, fe_candi)
                            skip_to_frame = fe_candi  # Skip frames already identified as a gradual transition
                            tor = 0  # Reset the temporary variable
                            break
                        continue
                    # Check if the standard deviation is above or equal to Tb
                    elif self.sd_array[after_frame_ind] >= self.tb:
                        tor = 0  # Reset the temporary variable
                        fe_candi = after_frame_ind - 1
                        # Process the gradual transition frames
                        self.summation(fs_candi, fe_candi)
                        skip_to_frame = fe_candi  # Skip frames already identified as a gradual transition
                        break

                    
    # Sum intensity standard deviations within a candidate range
    def summation(self, fs_candi, fe_candi):
        sd_total = 0

        # Loop through the standard deviation array for the given range
        for sd_ind in range(fs_candi, fe_candi + 1):
            sd_total += self.sd_array[sd_ind]

        # Check if the total standard deviation within the range is above the gradual transition threshold (Tb)
        if sd_total >= self.tb:
            fs = fs_candi
            fe = fe_candi
            # Add gradual transition frames to the results dictionary
            self.frame_results["fs"].append(fs + self.start_frame)
            self.frame_results["fe"].append(fe + self.start_frame)

    # Display sets of frames with cuts and gradual transitions
    def frame_sets(self):
        print("Cuts (Cs, Ce):")
        for num in range(len(self.frame_results["cs"])):
            cut = (self.frame_results["cs"][num], self.frame_results["ce"][num])
            print(str(cut), end="\t")
        print()

        print("Gradual Transitions (Fs, Fe):")
        for num in range(len(self.frame_results["fs"])):
            transition = (self.frame_results["fs"][num], self.frame_results["fe"][num])
            print(str(transition), end="\t")
        print()
    
