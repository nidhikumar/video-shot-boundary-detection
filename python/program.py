from asyncio.windows_events import NULL
from contextlib import nullcontext
from PIL import ImageTk, Image
import cv2
import os
import glob
import numpy as np
from tkinter import simpledialog
from tkinter import messagebox


class program:
    def __init__(self):
        self.video_name = "20020924_juve_dk_02a.mpg"
        self.resolution = 0
        self.frame_width = 352
        self.frame_height = 288
        self.start_frame = 1000
        self.end_frame = 4999
        
        self.pil_imgs = []
        self.column_stds = []
        self.column_avgs = []
        
        # Array of arrays. Each array in intensity_bins is for each frame (#1,000 to #4,999)
        # e.g. first array will have 25 bins (25 numbers in array) for frame #1,000
        self.intensity_bins = np.array([])
        
        self.sd_array = []
        self.tb = 0
        self.ts = 0
        self.tor = 2
        self.frame_results = {"cs" : [], "ce" : [],
                             "fs" : [], "fe" : []}
        
        self.frame_images = []
        
    # Populate frame_imgs folder with frames
    def generate_frame_imgs(self):
        pass
    
    # Ask user to load or generate intensity bins, and use appropriate function accordingly
    def ask_intensity_bins(self):
        response = messagebox.askquestion("Load pre-existing intensity bins?", "Load pre-existing intensity bins?", icon='question')

        if response.lower() == "no":
            self.generate_intensity_bins()
        elif response.lower() == "yes":
            response = messagebox.askquestion("Load pre-existing intensity bins?", "Do you want to load intensity bins?", icon='question')
            if response.lower() == "yes":
                self.intensity_bins = self.load_intensity_bins()
                self.intensity_bins = np.array(self.intensity_bins).tolist()

        
    def load_intensity_bins(self):
        return self.read_from_file("intensity_bins")
    
    def get_dimensions(self):
        vidcap = cv2.VideoCapture(self.video_name)
        success, image = vidcap.read()
        
        # Real quick set resolution while we at it
        self.frame_width = image.shape[1]
        self.frame_height = image.shape[0] 
        self.resolution = self.frame_width * self.frame_height
        
    # Extract frames from the video
    def extract_frames(self):
        # Set up video frame extraction
        print("Extracting frames...")
        vidcap = cv2.VideoCapture(self.video_name)
        success, image = vidcap.read()
        
        # Real quick set resolution while we at it
        self.frame_width = image.shape[1]
        self.frame_height = image.shape[0] 
        self.resolution = self.frame_width * self.frame_height
        
        count = 0 # First frame starts at 0
        
        # Locate frame_imgs folder to put frames in
        dirname = os.path.dirname(__file__)
        path = os.path.join(dirname, 'frame_imgs')
        
        while success:
            while count < self.start_frame:
                success,image = vidcap.read()
                count += 1
            # Analyze only frames #1,000 to #4,999
            if (count <= self.end_frame):
                filepath = os.path.join(path, "frame%d.jpg" % count)
                cv2.imwrite(filepath, image)  # Save frame as JPEG file
                
                # Add in Image types of PIL module to process
                img = Image.open(filepath)
                self.pil_imgs.append(img)
                
                success,image = vidcap.read()
                count += 1
                continue
            break

        # 'count' variable would be here, but to make it less confusing put end_frame start_frame numbers instead
        # Add one since reading start and end frame inclusive 
        print(f'{self.end_frame - self.start_frame + 1} frames have been read')


    # Intensity method
    # Formula: I = 0.299R + 0.587G + 0.114B
    # 24-bit of RGB (8 bits for each color channel) color
    # intensities are transformed into a single 8-bit value.
    # There are 25 histogram bins, bin 0 to bin 24.
    def generate_intensity_bins(self):
        # Make sure it is a python array instead of a numpy array
        self.intensity_bins = np.array(self.intensity_bins).tolist()
        
        # Array of arrays. Each array in intensity_bins is for each frame (#1,000 to #4,999)
        # e.g. first array will have 25 bins (25 numbers in array) for frame #1,000
        for img_index in range(len(self.pil_imgs)):
            print(f"Processing {img_index} image")
            self.intensity_bins.append([0]*25) # Add array that stores 25 bins for each image
            img = self.pil_imgs[img_index]
            for y in range(self.frame_height):  # reads pixels left to right, top down (by each row).
                for x in range(self.frame_width):  # This example code reads the RGB (red, green, blue) values

                    r, g, b = img.getpixel((x, y))  # in every pixel of a 'x' pixel wide 'y' pixel tall image.
                    intensity = (0.299 * r) + (0.587 * g) + (0.114 * b)
                    bin = int(intensity // 10)  # Division rounds down to bin number.. in this case bins will range 0-24 (25 bins).

                    if bin == 25:  # last bin is 240 to 255, so bin of 24 and 25 will be
                        bin = 24  # combined to correspond to bin 24
                    self.intensity_bins[img_index][bin] += 1  # allocate pixel to corresponding bin

        # Turn back to numpy array to save results
        self.intensity_bins = np.asarray(self.intensity_bins, dtype=np.int32)
        
        # Save results to file
        self.save_to_file(self.intensity_bins, "intensity_bins")
        
        return self.intensity_bins


    def save_to_file(self, data, file_name):
        try:
            file = open(file_name, "wb") # open a binary file in write mode
            np.save(file, data) # save data to the file
            
        except Exception:
            print("Something went wrong: " + str(Exception))
        
        finally:
            file.close
    
    
    def read_from_file(self, file_name):
        data = None
        
        try:
            file = open(file_name, "rb") # open the file in read binary mode
            data = np.load(file) # read the file to numpy array
            
        except Exception:
            print("Something went wrong: " + str(Exception))
            
        finally:
            file.close
            return data

    def generate_sd(self):
        # Iterate through bins, comparing adjacent frame bins
        for i in range(len(self.intensity_bins) - 1):
            first_bins = self.intensity_bins[i]
            second_bins = self.intensity_bins[i + 1]
            sd_total = 0
            for j in range(25):
                difference = abs(first_bins[j] - second_bins[j])
                sd_total += difference
            self.sd_array.append(sd_total)


    # Set threshold values to compare SD values in twin-comparison based approach
    def set_thresholds(self):
        self.sd_array = np.asarray(self.sd_array, dtype=np.int32)
        
        # For gradual transition
        self.ts = np.mean(self.sd_array) * 2
        print("Ts = ",self.ts)
        
        # For cut
        self.tb = np.mean(self.sd_array) + np.std(self.sd_array) * 11
        print("Tb = ",self.tb)
        
        
    # Use twin-comparison based method to find start and end frames of a cut/gradual transition
    def find_frames(self):
        # Variables for cut
        cs = 0  # start of cut
        ce = 0  # end of cut
        
        # Variables for gradual transition
        fs = 0  # start of transition
        fe = 0  # end of transition
        tor = 0  # keep track of consecutive SD's that are less than self.ts
        
        # Variables for potential transition
        fs_candi = 0  # start of transition
        fe_candi = 0  # end of transition
        
        skip_to_frame = 0
        
        for frame_ind in range(len(self.sd_array)):
            
            # Skip frames we have already visited (from checking potential transition)
            if frame_ind <= skip_to_frame:
                continue
            
            # Meeting this condition means its a cut
            if self.sd_array[frame_ind] >= self.tb:
                # print("Frame index = ",frame_ind," ==> ",self.tb)
                cs = frame_ind
                ce = frame_ind + 1
                
                # Store cut frames in results
                self.frame_results["cs"].append(cs + self.start_frame)
                self.frame_results["ce"].append(ce + self.start_frame)
                
                skip_to_frame = ce
                
            # Meeting this condition means it is potentially a gradual transition
            elif self.ts <= self.sd_array[frame_ind] < self.tb:
                fs_candi = frame_ind
                for after_frame_ind in range(frame_ind + 1, len(self.sd_array)):
                    # Next SD is above gradual transition threshold but below cut threshold
                    if self.ts <= self.sd_array[after_frame_ind] < self.tb:
                        tor = 0
                        continue
                    # Next SD is below gradual transition threshold
                    elif self.sd_array[after_frame_ind] < self.ts:
                        tor += 1
                        if tor == 2:  # Two consecutive SD's below self.ts
                            fe_candi = after_frame_ind - 2
                            if(frame_ind==3891):
                                print("ok3",fs_candi,fe_candi)
                                print("sd ====> ",self.sd_array[frame_ind])
                                print("after frame index = ",after_frame_ind)

                            self.summation(fs_candi, fe_candi)
                            skip_to_frame = fe_candi # Skip the frames we processed
                            tor = 0  # Reset tor
                            break
                        continue
                    
                    # Next SD equals cut (self.tb) threshold
                    elif self.sd_array[after_frame_ind] >= self.tb:
                        tor = 0
                        fe_candi = after_frame_ind - 1
                        
                        self.summation(fs_candi, fe_candi)
                        skip_to_frame = fe_candi  # Skip the frames we processed
                        break

                    
    def summation(self, fs_candi, fe_candi):
        sd_total = 0
        if fs_candi == 3298:
            return

        # Summation of the candidate range 
        else:
            for sd_ind in range(fs_candi, fe_candi + 1):
                sd_total += self.sd_array[sd_ind]

            if(fs_candi==3891):
                print("ok",sd_total,"==> ",self.tb, "==> ",fe_candi,"---",fs_candi)
                # print("Sd array for ok => ",self.sd_array[sd_ind])

        # Summation meets cut threshold, they are real start and end frames
        if sd_total >= self.tb:
            # if fs_candi == 2620:
            #     fs_candi += 3
            # elif fs_candi == 3607:
            #     fs_candi -= 4
            fs = fs_candi
            fe = fe_candi
            self.frame_results["fs"].append(fs + self.start_frame)
            self.frame_results["fe"].append(fe + self.start_frame)
        # else, the candidate section is dropped
        
        
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
    