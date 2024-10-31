# lustre-stripe-plotter
Graphically display the layout of a Lustre file.
Generate your file's layout YAML using `lfs getstripe -y <filename> > <filename.yaml>`
Run this code to:
- produce a cleaner, consistent, mirror-based YAML
- generate a jpg of the layout

Usage:
  `python striper.py <filename.yaml>`

Some notes:
- OST labels are 4-digit hex.
- Component ID labels are #<id>
- lcme_id labels are id<id>
- If objects are not yet allocated for a component, they are displayed in gray.
- The extents are plotted as far as the last well-defined component, not necessarily the full extent of the file. This is to avoid making the graphic unreadable for large files.
- We only label the OSTs when they are first introduced; thereafter any repeats are just identified by color. This allows a clearer identification of unique objects.
- Overstriped files are similarly colored, but are each explicitly labelled. (Eg. 001A, 001A would indicate two overstripes.)
- If the rendered stripes in a component would be too small to distinguish, it just displays the total number of stripes for the component.

  
Example of mirrored DoM PFL file:
  ![mirrored_pfl_orig](examples/mirpfldom.jpg)

## Install
It's just this python script, but you'll need some other python packages:

`pip install --upgrade numpy matplotlib seaborn yaml scipy`

## Known Issues
- The size of the first object after a DoM component shoud be drawn smaller by \<DoM size\>. I didn't bother to fix this.
- The image is drawn to scale. If the size of components relative to the size of the total image is too small, some of the components may drawn very close to each other, which makes it hard to read. I can imagine someone with better python skills than mine could come up with a magnifying-glass overlay...
