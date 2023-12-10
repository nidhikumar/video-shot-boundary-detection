# interface.py
# Program to set up the interface.

from tkinter import *
from PIL import ImageTk, Image
import glob, math, os
from program import program
from tkinter import messagebox


class interface(Frame):
    def __init__(self, master):

        # Initialize the program object and set up variables for frame dimensions and image lists
        self.program = program()
        self.frame_width = 500
        self.frame_height = 300
        self.frame_images_arr = []
        self.frame_images_list = []
        self.frame_desc = []
        self.frame_ranges = []
        self.master = master

        # Check for pre-existing frames and display loading label
        frames_present = self.get_existing_frame_images()
        
        self.loading_label = Label(self.master, text="Loading... Please wait.", font=("Helvetica", 16))
        self.loading_label.pack(side=TOP, pady=20)

        # Ask the user about frame conversion if frames are present
        if (frames_present):
            self.conversion()
            self.loading_label.pack_forget()
        
        # Ask the user how intensity bins should be loaded
        self.program.get_intensity_bins()
        
        # Generate standard deviations of intensity
        self.program.get_sd()
        
        # Calculate thresholds from standard deviations
        self.program.apply_threshold()
        
        # Calculate start and end frames with the Twin Comparison approach
        self.program.get_frames()
        
        # Print the sets of (Cs, Ce) and (Fs, Fe)
        self.program.frame_sets()
        
        print("Now loading interface...")
        
        # Populate self.frame_images with result frames so they appear in Listbox
        self.populate_frame_imgs()
        
        # Initialize the main frame
        Frame.__init__(self, master)
        self.master = master

        self.mainFrame = Frame(master)
        self.mainFrame.columnconfigure(0, weight=1)
        self.mainFrame.columnconfigure(1, weight=5)
        self.mainFrame.rowconfigure(0, weight=1)
        self.mainFrame.pack(fill='both', expand=True)
        
        # Load a default image and display it in a Label
        img = Image.open('default.jpg')
        img = img.resize((self.frame_width, self.frame_height), Image.ANTIALIAS)
        self.chosen_frame = ImageTk.PhotoImage(img)
        self.frameLabel = Label(self.mainFrame, width=500, bg="black", image=self.chosen_frame)
        self.frameLabel.grid(column=1, row=0, sticky=NS, padx=5, pady=10)
    
        # Set up Play button
        self.play_text = StringVar(value="Play")
        self.play_button = Button(master, bg="gray", textvariable=self.play_text, command=self.play_frame, fg="white", padx=8, pady=5)
        self.play_button.pack(side=TOP, pady=8)
    
        # Create a frame for thumbnails below the Play button
        self.thumbnail_frame = Frame(master, bg="white", height=self.frame_height//4, width=(self.frame_width * len(self.frame_ranges) )//4)
        self.thumbnail_frame.pack(side=BOTTOM, pady=10, fill=BOTH, expand=True)

        # Populate the thumbnail frame with thumbnail images
        self.populate_thumbnail_images()

    # Method to set the selected index when a thumbnail is clicked
    def set_selected_index(self, index):
        # Store the selected index for future reference
        self.selected_index = index
        frame_set = self.frame_ranges[index]
        i = frame_set[0]
        # Retrieve and display the selected image frame in the main Label
        image_frame = self.frame_images_list[i - self.program.start_frame]
        self.frameLabel.configure(image=image_frame)
        self.frameLabel.image = image_frame

    # Method to play frames sequentially
    def play_frame(self, frame=0):
        # Check if a thumbnail is selected
        if hasattr(self, 'selected_index'):
            selected_frame_index = self.selected_index
            frame_set = self.frame_ranges[selected_frame_index]
            i = frame_set[0] + frame
            # Check if the frame is within the selected range
            if i - self.program.start_frame > frame_set[1] - self.program.start_frame:
                return
            pil_frame = self.frame_images_list[i - self.program.start_frame]
            # Update the main Label with the current frame
            self.frameLabel.configure(image=pil_frame)
            self.frameLabel.image = pil_frame
            # Schedule the next frame to be played after a delay
            root.after(15, self.play_frame, frame + 1)
        else:
            # If no thumbnail is selected, show a warning message
            messagebox.showinfo("Warning", "Please click a thumbnail before playing.")

    def populate_thumbnail_images(self):
        o_thumbnail_width = 500
        o_thumbnail_height = 400
        # Increase the size of the thumbnail images
        thumbnail_scale_factor = 0.34  # You can adjust this factor based on your preference

        self.thumbnail_width = o_thumbnail_width // (10 * thumbnail_scale_factor)
        self.thumbnail_height = o_thumbnail_height // (10 * (thumbnail_scale_factor + 0.07))
        self.padding_x = 1  # Adjust the horizontal padding
        self.padding_y = 1  # Adjust the vertical padding

        for i in range(len(self.frame_ranges)):
            frame = self.frame_ranges[i][0]
            path = f'frame_images/frame{frame}.jpg'

            im = Image.open(path)
            im.thumbnail((self.thumbnail_width, self.thumbnail_height), Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(im)

            # Calculate row and column in the 3x9 grid
            row = i // 10
            col = i % 10

            # Determine the type of transition for the frame
            transition_type = self.get_transition_type(frame)

            # Create thumbnail label
            thumbnail_label = Label(self.thumbnail_frame, image=photo, width=self.thumbnail_width, height=self.thumbnail_height)
            thumbnail_label.grid(row=row * 2, column=col, padx=(self.padding_x, 0), pady=(self.padding_y, 0))

            # Save a reference to the image to prevent it from being garbage collected
            thumbnail_label.image = photo

            # Create label for frame number with transition type
            frame_number_label = Label(self.thumbnail_frame, text=f"Frame {frame} ({transition_type})", fg="white", bg="black")
            frame_number_label.grid(row=row * 2 + 1, column=col, padx=(self.padding_x, 0), pady=(self.padding_y, 0))

            # Bind the set_selected_index method to the thumbnail label
            thumbnail_label.bind('<Button-1>', lambda event, index=i: self.set_selected_index(index))

            # Raise the frame number label to be on top
            frame_number_label.lift()

    # Method to get the type of transition for a frame
    def get_transition_type(self, frame):
        # Your logic to determine the transition type based on frame number
        # For example, you can check if the frame is in the list of Cut frames
        if frame-1 in self.program.frame_results["cs"]:
            return "Cut"
        # Or check if the frame is in the list of Gradual Transition frames
        elif frame-1 in self.program.frame_results["fs"]:
            return "GT"
        # If the frame is not identified as Cut or Gradual Transition, you can return an appropriate value
        else:
            return "Unknown"


    # Method to convert images and store them in a list
    def convert_images(self):
        # Iterate over all image files in the 'frame_images' folder
        for infile in (glob.glob('frame_images/*.jpg')):
            # Open each image file
            im = Image.open(infile)

            # Resize the image to fit the frame dimensions
            imResize = im.resize((self.frame_width, self.frame_height), Image.ANTIALIAS)
            
            # Convert the resized image to PhotoImage format
            photo = ImageTk.PhotoImage(imResize)

            # Append the PhotoImage to the list of frame images
            self.frame_images_list.append(photo)

    # Event "listener" for listbox change, updates the preview by index
    def update_preview_by_index(self, index):
        # Retrieve the PhotoImage at the specified index
        selected_frame_image = self.frame_images_arr[index]

        # Update the main Label with the selected frame image
        self.frameLabel.configure(image=selected_frame_image)
    
    # Method to populate frame ranges and descriptions
    def populate_frame_imgs(self):
        # Initialize lists to store start and end frames
        start_frames = [self.program.start_frame]
        end_frames = [self.program.end_frame]

        # Append Ce frames as start frames
        for ce_frame in self.program.frame_results["ce"]:
            start_frames.append(ce_frame)
        # Append Fs + 1 frames as start frames
        for fs_frame in self.program.frame_results["fs"]:
            start_frames.append(fs_frame + 1)
        start_frames.sort()

        # Append Cs frames as end frames
        for cs_frame in self.program.frame_results["cs"]:
            end_frames.append(cs_frame)
        # Append Fs frames as end frames
        for fs_frame in self.program.frame_results["fs"]:
            end_frames.append(fs_frame)
        end_frames.sort()

        # Iterate over the start frames to create shot ranges
        for i in range(len(start_frames)):
            # Skip the first iteration (index 0)
            if i == 0:
                continue
            # Create a tuple representing the shot range (start frame, end frame)
            shot = (start_frames[i], end_frames[i])
            self.frame_ranges.append(shot)
            # Add the start frame description to the list
            self.frame_desc.append(str(start_frames[i]))

        # Iterate over the frame ranges to load and convert images
        for shot in self.frame_ranges:
            # Generate the file path for the frame image
            path = f'frame_images/frame{shot[0]}.jpg'
            
            # Open the image file
            im = Image.open(path)

            # Resize the image to fit the frame dimensions
            imResize = im.resize((self.frame_width, self.frame_height), Image.ANTIALIAS)
            
            # Convert the resized image to PhotoImage format
            photo = ImageTk.PhotoImage(imResize)

            # Append the PhotoImage to the list of frame images
            self.frame_images_arr.append(photo)

    # Method to check if there are pre-existing frame images
    def get_existing_frame_images(self):
        # Locate the 'frame_images' folder that stores the frames
        dirname = os.path.dirname(__file__)
        path = os.path.join(dirname, 'frame_images')

        # Get the list of directories in the folder
        dir = os.listdir(path)
  
        # Check if the list is empty or not
        if len(dir) == 0:  
            print("There are no pre-existing frame images.")
            print("Frame images will now be extracted into 'frame_images' folder")

            # Extract frames if none exist
            self.program.extract_frames()
            return False
        else:
            return True 

    def conversion(self):
        # Use messagebox.askquestion for both prompts
        convert = messagebox.askquestion("Convert from pre-existing frames?", "Convert from pre-existing frames?", icon='question')

        while True:
            convert = convert.lower()
            if convert == "no":
                self.program.extract_frames()
                self.program.get_dimensions()
                break
            elif convert == "yes":
                self.convert_images()
                self.program.get_dimensions()
                break
            convert = messagebox.askquestion("Convert from pre-existing frames?", "Please choose Yes or No", icon='question')

# Executable section.
if __name__ == '__main__':
    root = Tk()
    root.title('CSS 584 - Video Shot Boundary Detection')

    # Maximize the window
    root.state('zoomed')

    root.bind('<Escape>', lambda event: root.attributes('-fullscreen', False))  # Press Esc to exit full screen
    root.resizable(0, 0)

    imageViewer = interface(root)

    root.mainloop()
