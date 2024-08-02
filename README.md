# lustre-stripe-plotter
Graphically display the layout of a Lustre file.
Generate your file's layout YAML using 'lfs getstripe -y <filename> > <filename.yaml>'
Run this code to:
- produce cleaned-up, valid YAML (which Lusttre getstripe -y does not produce)
- generate a jpg of the layout

Usage:
  python striper.py <filename.yaml>

Some notes:
- The graphic extends as far as the last well-defined component, not necessarily the full extent of the file. This is to avoid making the graphic unreadable for large files.
- We only label the OSTs when they are first introduced; thereafter any repeats are just identified by color. This allows a clearer identification of unique objects.
- Overstriped files are similarly colored, but are each explicitly labelled. (Eg. 001a, 001a would indicate two stripes on OST001A)
- OST labels are 4-digit hex.
- Component ID labels are #<id>
- lcme_id labels are id<id>
- The size of the first object after a DoM component shoud be drawn smaller by DoM size. I didn't bother to fix this.
  
  ![mirrored_pfl_orig](https://media.github.hpe.com/user/38993/files/f72bf8e5-3b9d-4c37-ae00-51321a6fb1f6)
