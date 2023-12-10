# interface.py
# Program to set up the interface.

from tkinter import *
from PIL import ImageTk, Image
import glob, math, os
from program import program
from tkinter import messagebox


class interface(Frame):
    # Constructor
    def __init__(self, master):

        self.program = program()
        self.frame_width = 500
        self.frame_height = 300
        self.frame_imgs = []
        self.pil_frame_imgs = []
        self.frame_desc = []
        self.frame_ranges = []
        self.master = master

        # Check for pre-exisiting frames. If there are no frames, it will generate them.
        frames_present = self.check_frame_imgs()
        
        self.loading_label = Label(self.master, text="Loading... Please wait.", font=("Helvetica", 16))
        self.loading_label.pack(side=TOP, pady=20)

        # If there are frames present in frame_imgs, ask the user if they want to re-extract the
        # frames or skip extraction.
        if (frames_present):
            self.ask_conversion()
            self.loading_label.pack_forget()
        
        # Ask user how intensity bins should be loaded
        self.program.ask_intensity_bins()
        
        # Generate SD values
        self.program.generate_sd()
        
        # Calculate thresholds from SD values
        self.program.set_thresholds()
        
        # Calculate start and end frames with Twin-comparison based approach
        self.program.find_frames()
        
        # Print the sets of (Cs, Ce) and (Fs, Fe).
        self.program.frame_sets()
        
        print("Now loading interface...")
        
        # Populate self.frame_imgs with result frames so they appear in Listbox
        self.populate_frame_imgs()
        
        # Generate cut's start and end frames 
        self.program.generate_frame_imgs()
        
        # Generate window
        Frame.__init__(self, master)
        self.master = master

        # Create Main frame.
        self.mainFrame = Frame(master)
        self.mainFrame.columnconfigure(0, weight=1)
        self.mainFrame.columnconfigure(1, weight=5)
        self.mainFrame.rowconfigure(0, weight=1)
        self.mainFrame.pack(fill='both', expand=True)
        
        # Create label that shows frames
        img = Image.open('default.jpg')
        img = img.resize((self.frame_width, self.frame_height), Image.ANTIALIAS)
        self.chosen_frame = ImageTk.PhotoImage(img)
        self.frameLabel = Label(self.mainFrame, width=500, bg="black", image=self.chosen_frame)
        self.frameLabel.grid(column=1, row=0, sticky=NS, padx=10, pady=10)
    
        # Button to press play to play the frame's corresponding shot
        self.play_text = StringVar(value="Play")
        self.play_button = Button(master, bg="gray", textvariable=self.play_text, command=self.play_frame, fg="white", padx=8, pady=5)
        # self.play_button.pack(side=BOTTOM, pady=8)
        self.play_button.pack(side=TOP, pady=8)
    

        # Create a frame for thumbnails below the Play button
        self.thumbnail_frame = Frame(master, bg="white", height=self.frame_height//4, width=(self.frame_width * len(self.frame_ranges) )//4)
        # self.thumbnail_frame.pack(side=BOTTOM, pady=10)
        self.thumbnail_frame.pack(side=BOTTOM, pady=10, fill=BOTH, expand=True)

        # self.thumbnail_frame.grid_columnconfigure(0, weight=1)
        # self.thumbnail_frame.grid(row=1, column=1, sticky="w", pady=10)
        

        # Populate the thumbnail frame with thumbnail images
        self.populate_thumbnail_images()

    # New method to set the selected index when a thumbnail is clicked
    def set_selected_index(self, index):
        self.selected_index = index
        frame_set = self.frame_ranges[index]
        i = frame_set[0]
        pil_frame = self.pil_frame_imgs[i - self.program.start_frame]
        self.frameLabel.configure(image=pil_frame)
        self.frameLabel.image = pil_frame

    def play_frame(self, frame=0):
        if hasattr(self, 'selected_index'):
            selected_frame_index = self.selected_index
            frame_set = self.frame_ranges[selected_frame_index]  # get the shot start and end range
            i = frame_set[0] + frame
            if i - self.program.start_frame > frame_set[1] - self.program.start_frame:  # done at last frame of shot
                return
            pil_frame = self.pil_frame_imgs[i - self.program.start_frame]
            self.frameLabel.configure(image=pil_frame)
            self.frameLabel.image = pil_frame
            root.after(15, self.play_frame, frame + 1)
        else:
            print("Please select a frame from the Listbox or click a thumbnail before playing.")
    

    # Populate the thumbnail frame with thumbnail images
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
            path = f'frame_imgs/frame{frame}.jpg'

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


    # Turn frames into pil images for tkinter to display
    def convert_to_pil_imgs(self):
        # Add each frame into self.frame_imgs
        for infile in (glob.glob('frame_imgs/*.jpg')):
            im = Image.open(infile)

            # Resize to fit the frame
            imResize = im.resize((self.frame_width, self.frame_height), Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(imResize)

            # Add the images to the list.
            self.pil_frame_imgs.append(photo)
        
    # Event "listener" for listbox change.
    def update_preview_by_index(self, index):
        self.chosen_frame = self.frame_imgs[index]
        self.frameLabel.configure(image=self.chosen_frame)
    
    # Read in all frame images from the folder frame_imgs, then convert to
    # a image that can be presented in tkinter
    def populate_frame_imgs(self):
        start_frames = [self.program.start_frame]
        # Ce, Fs + 1 are first frame of previous shot
        for ce_frame in self.program.frame_results["ce"]:
            start_frames.append(ce_frame)
        for fs_frame in self.program.frame_results["fs"]:
            start_frames.append(fs_frame + 1)
        start_frames.sort()
            
        end_frames = [self.program.end_frame]
        
        # Cs, Fs are end frames of previous shot
        for cs_frame in self.program.frame_results["cs"]:
            end_frames.append(cs_frame)
        for fs_frame in self.program.frame_results["fs"]:
            end_frames.append(fs_frame)
        end_frames.sort()
        
        for i in range(len(start_frames)):
            if i == 0:
                continue
            shot = (start_frames[i], end_frames[i])
            self.frame_ranges.append(shot)
            self.frame_desc.append(str(start_frames[i]))            

        for shot in self.frame_ranges:
            path = f'frame_imgs/frame{shot[0]}.jpg'
            
            im = Image.open(path)

            # Resize to fit the frame
            imResize = im.resize((self.frame_width, self.frame_height), Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(imResize)

            # Add the images to the list.
            self.frame_imgs.append(photo)
        
    # Check if the 'frame_imgs' folder has any pre-existing frames
    def check_frame_imgs(self):
        # Locate frame_imgs folder that stores the frames
        dirname = os.path.dirname(__file__)
        path = os.path.join(dirname, 'frame_imgs')

        # Getting the list of directories
        dir = os.listdir(path)
  
        # Checking if the list is empty or not
        if len(dir) == 0:  
            print("There are no pre-existing frame images.")
            print("Frame images will now be extracted into 'frame_imgs' folder")

            self.program.extract_frames()
            return False

        else:
            return True 

    def ask_conversion(self):
        # Use messagebox.askquestion for both prompts
        convert = messagebox.askquestion("Convert from pre-existing frames?", "Convert from pre-existing frames?", icon='question')

        while True:
            convert = convert.lower()
            if convert == "no":
                self.program.extract_frames()
                self.program.get_dimensions()
                break
            elif convert == "yes":
                self.convert_to_pil_imgs()
                self.program.get_dimensions()
                break
            convert = messagebox.askquestion("Convert from pre-existing frames?", "Please choose Yes or No", icon='question')

# Executable section.
if __name__ == '__main__':
    root = Tk()
    root.title('Video Shot Boundary Detection App')

    # Maximize the window
    root.state('zoomed')

    root.bind('<Escape>', lambda event: root.attributes('-fullscreen', False))  # Press Esc to exit full screen
    root.resizable(0, 0)

    imageViewer = interface(root)

    root.mainloop()