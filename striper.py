#!/usr/bin/env python
# Copyright 2024 Hewlett Packard Enterprise Development LP
# Authors: nathan.rutman@hpe.com


import sys
import yaml
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.ticker import MultipleLocator, MaxNLocator, FuncFormatter
import seaborn as sns
import random

def convert_simple_yaml(data):
  """ Old v1 single-component
  """

  if 'lmm_layout_gen' not in data:
    print("Error: Not a stripe YAML file -- getstripe -y?")
    return None

  component_data = {
    'component_id': "component0",
    'lcme_extent': {'e_start': 0, 'e_end': 'EOF'},
    'lcme_id': 0,
    'lcme_flags': 0,
    'sub_layout': data
  }
  mirrors = {}
  mirrors[1] = {'lcme_mirror_id': 1, 'components': []}
  mirrors[1]['components'].append(component_data)

  # Create the corrected YAML structure
  corrected_data = {
      'lcm_layout_gen': data.get('lmm_layout_gen'),
      'lcm_mirror_count': 1,
      'lcm_entry_count': 1,
      'mirrors': list(mirrors.values())
  }
  return corrected_data

def convert_yaml(data):
  """ Converts misformatted lfs getstripe YAML to correct YAML
  """

  if 'lcm_layout_gen' not in data:
    return convert_simple_yaml(data)

  lcm_layout_gen = data.pop('lcm_layout_gen')
  lcm_mirror_count = data.pop('lcm_mirror_count')
  lcm_entry_count = data.pop('lcm_entry_count')

  # Group components by lcme_mirror_id
  mirrors = {}
  for component_name, component_data in data.items():
    mirror_id = component_data.pop('lcme_mirror_id')
    component_data['component_id'] = component_name
    component_data['lcme_extent'] = {'e_start': component_data.pop('lcme_extent.e_start'),
                                'e_end': component_data.pop('lcme_extent.e_end')}
    if mirror_id not in mirrors:
      mirrors[mirror_id] = {'lcme_mirror_id': mirror_id, 'components': []}
    mirrors[mirror_id]['components'].append(component_data)

  # Create the corrected YAML structure
  corrected_data = {
      'lcm_layout_gen': lcm_layout_gen,
      'lcm_mirror_count': lcm_mirror_count,
      'lcm_entry_count': lcm_entry_count,
      'mirrors': list(mirrors.values())
  }
  return corrected_data


def parse_yaml(data):
  """ Parse stripe YAML into components
  """

  # Check if mirrors key exists
  if 'mirrors' not in data:
      print("Error: YAML file missing 'mirrors' key")
      return None  # Or handle the missing key in another way
  
  components = []
  for mirror_data in data['mirrors']:
    for component_data in mirror_data['components']:
        sublayout = component_data['sub_layout']
        if 'lmm_stripe_size' in sublayout:
            size = sublayout['lmm_stripe_size']
        if 'lmm_extension_size' in sublayout:
            size =  sublayout['lmm_extension_size']
        component = {
        'id': component_data['lcme_id'],
        'mirror': mirror_data['lcme_mirror_id'],
        'start': component_data['lcme_extent']['e_start'],
        'end': component_data['lcme_extent']['e_end'],
        'flags': component_data['lcme_flags'],
        'stripe_size': size,
        'eofend': component_data['lcme_extent']['e_end'] 
            if component_data['lcme_extent']['e_end'] != 'EOF'
            else component_data['lcme_extent']['e_start'] + sublayout['lmm_stripe_count'] * size,
        'pattern': sublayout['lmm_pattern'],
        'pool': sublayout['lmm_pool'] 
            if 'lmm_pool' in sublayout
            else sublayout['lmm_pattern'],
        'count': sublayout['lmm_stripe_count']
        }

        if 'lmm_stripe_count' in sublayout and sublayout['lmm_stripe_count'] > 0:
            component['stripes'] = []
            for stripe_data in sublayout.get('lmm_objects', []):
                component['stripes'].append({
                'l_ost_idx': stripe_data['l_ost_idx'],
                'l_fid': stripe_data['l_fid']
                })

        components.append(component)

  return components

def format_bytes(x, pos):
    """Formats a number in bytes as a string in megabytes."""
    return f"{x / 1048576:.0f} MB"

def draw_extent_diagram(components):
  """ Plot mirrors and components
  """

  fig, ax = plt.subplots()
  maxext = max(component['eofend'] for component in components)
  ax.set_xlim(0, maxext)
  mirrors = max(component['mirror'] for component in components)
  mirrors = max(mirrors, 1)
  ax.set_ylim(mirrors, 0)  # Invert y-axis


  # Access seaborn's color palette
  compcolors = sns.color_palette("pastel", n_colors=len(components))
  #stripecolors = ['blue', 'green', 'red', 'purple', 'orange','lightgray']  # Replace with your desired colors
  stripecolors = sns.color_palette("muted", n_colors=20)

  # Plot components
  for i, component in enumerate(components):
    start, end, mirror = component['start'], component['end'], component['mirror']
    # Mirrored files start counting at 0
    mirror = max(mirror, 1) - 1
    if end == 'EOF':
       end = maxext
    color = compcolors[i % len(compcolors)]
    rect = patches.Rectangle((start, mirror), end - start, 0.8, linewidth=1, edgecolor=color, facecolor=color)
    ax.add_patch(rect)
    # Add component label with lmm_pattern
    if component['pattern'] == 'mdt':
        ax.text((start + end) / 2, mirror + 0.4, f"mdt", ha='center', fontsize=10, rotation=90)
    else:
        label1 = f"#{i} ({component.get('pool', 'N/A')})"
        label2 = f"id{component['id']}"
        ax.text((start + end) / 2, mirror + 0.08, label1, ha='center')
        ax.text((start + end) / 2, mirror + 0.17, label2, ha='center')

    # Plot stripes inside component
    stripe_width = component['stripe_size']
    assert(stripe_width > 0)
    stripe_start = start
    #print(i, start, end, stripe_width, component['eofend'], maxext)
    # Don't draw individual stripes if too tiny
    if (stripe_width > end / 100) and ('stripes' in component):
        olabel = True
        stripes = len(component['stripes'])
        while (stripe_start < end):
          for i in range(component['count']):
              #print(i, stripes)
              if i < stripes:
                  stripe = component['stripes'][i]
                  color = stripecolors[stripe['l_ost_idx'] % len(stripecolors)]
              else:
                  color = 'gray'
                  olabel= False
              stripe_rect = patches.Rectangle((stripe_start, mirror + 0.2), stripe_width, 0.6, linewidth=0.5, edgecolor='black', facecolor=color)
              ax.add_patch(stripe_rect)
              if olabel:
                  ax.text(stripe_start + stripe_width/2, mirror + 0.6, f"{stripe['l_ost_idx']:04x}", ha='center', rotation=90)
              stripe_start += stripe_width
              if stripe_start >= end:
                  break
          olabel = False

  ax.set_yticks([])
  ax.set_xlabel("Extent")

  # Set ticks on MB boundaries, max of 10.
  ticks=int(maxext/1048576/10+1.0)
  ax.xaxis.set_major_locator(MultipleLocator(ticks*1048576))
  # Format x-axis ticks as megabytes
  formatter = FuncFormatter(format_bytes)
  ax.xaxis.set_major_formatter(formatter)
  # Rotate x-axis tick labels
  plt.xticks(rotation=90)

  fig.set_figwidth(12)
  fig.set_figheight(mirrors * 2)
  #plt.show()
  return plt


def read_yaml(yaml_file):
  print("file:", yaml_file)
  with open(yaml_file, 'r') as f:
    try:
        data = yaml.safe_load(f)
        print("yaml:", data)
    except yaml.YAMLError as exc:
        print(exc)
        return None
  return data


def get_filename_without_extension(filepath):
  last_dot = filepath.rfind('.')
  if last_dot == -1:
    return filepath  # No extension found
  else:
    return filepath[:last_dot]
  

if __name__ == "__main__":
  if len(sys.argv) != 2:
      print("Usage: python striper.py <yaml_file>")
      exit(1)
  yaml_file = sys.argv[1]
  data = read_yaml(yaml_file)
  if data == None:
      print("Error: can't parse yaml. Did you use getstripe -y?")
      exit(1)
  if 'mirrors' not in data:
     data = convert_yaml(data)
  print("cleaned:\n")
  print(yaml.dump(data))
  components = parse_yaml(data)
  if components == None:
      print("Error: can't parse striping")
      exit(1)
  plt = draw_extent_diagram(components)
  filename = get_filename_without_extension(yaml_file) + ".jpg"
  plt.savefig(filename, dpi=100, bbox_inches='tight')
  print("Saved jpg image:", filename)
  exit(0)
