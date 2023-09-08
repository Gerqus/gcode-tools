# Importing necessary modules
import re
import os
import sys

def normalize_gcode_flow(input_file_path, max_flow_rate_cap=None):
    # Initialize variables
    e_value = 0
    f_value = 0
    is_relative_mode = False
    min_flow_rate = float('inf')
    max_flow_rate = float('-inf')
    
    # Calculate the nozzle area
    nozzle_diameter = 0
    if len(sys.argv) > 2:
        nozzle_diameter = float(sys.argv[2])
    while nozzle_diameter <= 0:
        nozzle_diameter = float(input("Enter the nozzle diameter in mm: "))
        if nozzle_diameter <= 0:
            print("The nozzle diameter must be a positive number. Please try again.")

    print("Using nozzle diameter: " + str(nozzle_diameter) + "mm")
    nozzle_area = 3.14159 * (nozzle_diameter / 2) ** 2
    
    # Initialize lists to hold original and modified G-code lines
    original_gcode = []
    modified_gcode = []
    
    # Read the G-code file
    with open(input_file_path, 'r') as file:
        original_gcode = file.readlines()
    
    # Process each line in the G-code file
    for line in original_gcode:
        # Check for extrusion mode (absolute or relative)
        if "G90" in line:
            is_relative_mode = False
        elif "G91" in line:
            is_relative_mode = True
        
        # Extract E and F values
        e_match = re.search(r"E(-?\d+(\.\d+)?)", line)
        f_match = re.search(r"F(\d+(\.\d+)?)", line)
        
        if e_match:
            e_value_new = float(e_match.group(1))
            if is_relative_mode:
                e_value += e_value_new  # Update E value incrementally in relative mode
            else:
                e_value = e_value_new  # Update E value directly in absolute mode
        
        if f_match:
            f_value = float(f_match.group(1))
        
        # Calculate flow rate if both E and F values are available
        if e_value and f_value:
            time_for_move = e_value / f_value * 60  # Convert F from mm/min to mm/s
            flow_rate = (nozzle_area * e_value) / time_for_move  # Flow rate in mm³/s
            min_flow_rate = min(min_flow_rate, flow_rate)
            max_flow_rate = max(max_flow_rate, flow_rate)
            
            # Normalize flow rate if it exceeds the cap
            if max_flow_rate_cap and flow_rate > max_flow_rate_cap:
                scaling_factor = max_flow_rate_cap / flow_rate
                f_value *= scaling_factor  # Scale down the F value
                
                # Replace E and F values in the G-code line
                line = re.sub(r"F\d+(\.\d+)?", f"F{f_value}", line)
        
        # Append the (potentially modified) line to the modified G-code list
        modified_gcode.append(line)
    
    # Show max and min flow rates (skipping user confirmation as it requires user input)
    print(f"Max flow rate found: {max_flow_rate} mm³/s")
    print(f"Min flow rate found: {min_flow_rate} mm³/s")
    
    while max_flow_rate_cap == None or max_flow_rate_cap <= 0 or isinstance(max_flow_rate_cap, float) == False:
        max_flow_rate_cap = None
        try:
            max_flow_rate_cap = float(input("Enter the flow rate cap in mm³/min: ")) if max_flow_rate_cap is None else max_flow_rate_cap
        except ValueError:
            print("The flow rate cap must be a number. Please try again.")
            continue
        if max_flow_rate_cap <= 0:
            print("The flow rate cap must be a positive number. Please try again.")
            continue

    # Check if normalization is needed
    if max_flow_rate <= max_flow_rate_cap:
        print("The flow rate cap requirement is met. No further action is needed.")
        return
    else:
        # Write the modified G-code to a new file
        output_file_path = os.path.splitext(input_file_path)[0] + f"_flow_{max_flow_rate_cap}_normalized.gcode"
        suffix_number = 0
        while os.path.isfile(output_file_path):
            suffix_number += 1
            output_file_path = os.path.splitext(input_file_path)[0] + f"_flow_{max_flow_rate_cap}_normalized_{suffix_number}.gcode"
        with open(output_file_path, 'w') as file:
            file.writelines(modified_gcode)
        print(f"Normalized G-code has been saved to {output_file_path}.")

if __name__ == "__main__":
    # Get the input file path from the user
    input_file_path = ""
    if len(sys.argv) > 1:
        input_file_path = sys.argv[1]
    else:
        input_file_path = input("Enter the path to your input G-code file: ")

    if not os.path.isfile(input_file_path):
        print("The input file path is invalid (not a file / file does not exist). Please try again.")
        exit()

    if not input_file_path.endswith(".gcode"):
        print("The input file must be a G-code file. Please try again.")
        exit()

    print("Calculating file " + input_file_path + "...")

    # Normalize the flow rate
    normalize_gcode_flow(input_file_path)
