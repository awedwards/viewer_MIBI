from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
from random import randrange
import sys
import imageio
import napari
import exifread
import pathlib
import h5py
import numpy as np

class App(QWidget):

    def __init__(self):
        super().__init__()
        
        # Limits to the linear monochrome LUTs within napari
        self.available_LUTs = ['blue', 'cyan', 'gray', 'green', 'magenta', 'red', 'yellow']

        self.run_all()

    # Prompt to select MIBItiff. No error handling.
    def get_working_directory(self, message):
        path_str = (QFileDialog.getOpenFileName(self, message))
        return pathlib.Path(str(path_str[0]))

    def get_saving_directory(self, message):
        path_str = (QFileDialog.getSaveFileName(self, message))
        return pathlib.Path(str(path_str[0]))

    # Opens the tiff file
    def open_tiff(self, file_name):
        image = imageio.mimread(file_name, multifile=True)
        return image

    # Gets the channels from the tags
    def get_tags(self, file_name, num_images):
        f = open(file_name, 'rb')
        tags = exifread.process_file(f)
        channel_list = [str(tags['Image PageName']), str(tags['Thumbnail PageName'])]
        for n in range(2, num_images):
            channel_list.append(str(tags['IFD ' + str(n) + ' PageName']))

        return channel_list

    # Determine how many channels there should be
    def get_image_length(self, image):
        num_images = len(image)
        return num_images

    # launches napari with the fle and channel names
    def launch_napari(self, image, channel_names, LUTs):
        with napari.gui_qt():
            self.viewer = napari.Viewer()

            self.file_menu = self.viewer.window.file_menu
            self.add_h5_export_menu()

            for c in range(len(channel_names)):
                self.viewer.add_image(image[c], name=channel_names[c], visible=False)
                self.viewer.layers[c].name = channel_names[c]
                self.viewer.layers[c].colormap = LUTs[randrange(len(LUTs))]
                self.viewer.layers[c].opacity = 1.0
                self.viewer.layers[c].blending = 'additive'
                self.viewer.layers[c].interpolation = 'gaussian'
    
    def h5_export_all(self):
        export_path = self.get_saving_directory('Save all channels as')
        
        with h5py.File(export_path,'w') as f:
            dset = f.create_dataset("data", np.shape(self.im), data=self.im)
            metadata_set = f.create_dataset("channels", data=np.array(self.channels,dtype=h5py.string_dtype(encoding='utf-8')))
            
    def h5_export_visible(self):

        indices = []
        channels_subset = []

        for i,layer in enumerate(self.viewer.layers):
            if layer.visible:
                indices.append(i)
                channels_subset.append(layer.name)
        
        image_to_save = self.im[indices,:,:]

        export_path = self.get_saving_directory('Save visible channels as')

        with h5py.File(export_path, 'w') as f:
            dset = f.create_dataset("data", np.shape(image_to_save), data=image_to_save)
            metadata_set = f.create_dataset("channels", data=np.array(channels_subset,dtype=h5py.string_dtype(encoding='utf-8')))
            
    def add_h5_export_menu(self):
        self.h5_menu = self.file_menu.addMenu('Export as H5...')
        self.h5_exportall_menu = self.h5_menu.addAction('All channels')
        self.h5_exportvisible_menu = self.h5_menu.addAction('Only visible channels')

        self.h5_exportall_menu.triggered.connect(self.h5_export_all)
        self.h5_exportvisible_menu.triggered.connect(self.h5_export_visible)

    # Runs the program
    def run_all(self):
        self.mibi_path = self.get_working_directory("Select MIBI image File:")
        
        if str(self.mibi_path).endswith('.tif') or str(self.mibi_path).endswith('.tiff'):
            self.im = np.array(self.open_tiff(self.mibi_path))
            self.num_channels = self.get_image_length(self.im)
            self.channels = self.get_tags(self.mibi_path, self.num_channels)

        elif str(self.mibi_path).endswith('.h5') or str(self.mibi_path).endswith('.hdf5'):
            with h5py.File(self.mibi_path, 'r') as f:
                
                self.im = np.array(f['data'])
                self.channels = list(f['channels'])
                
        self.launch_napari(self.im, self.channels, self.available_LUTs)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())