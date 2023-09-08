# Importing necessary modules
import enum
import re
import os
import sys

# min/max normalize by enum
class NormalizeBy(enum.Enum):
    MIN = 'min'
    MAX = 'max'

def normalize_gcode_flow(input_file_path, flow_rate_cap=None):
    # Initialize variables
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

    # filament diameter
    filament_diameter = 0
    if len(sys.argv) > 3:
        filament_diameter = float(sys.argv[3])
    while filament_diameter <= 0:
        filament_diameter = float(input("Enter the filament diameter in mm (probably 1.75 or 3): "))
        if filament_diameter <= 0:
            print("The filament diameter must be a positive number. Please try again.")

    print("Using filament diameter: " + str(filament_diameter) + "mm")
    filament_crossection_area = 3.14159 * (nozzle_diameter / 2) ** 2
    
    # Initialize lists to hold original and modified G-code lines
    original_gcode = []
    modified_gcode = []
    
    # Read the G-code file
    with open(input_file_path, 'r') as file:
        original_gcode = file.readlines()
    
    last_f_used = None
    # Process each line in the G-code file
    for line in original_gcode:
        if not line.startswith(("G0", "G1", "G2", "G3")):
            continue
        
        # Extract F value
        f_match = re.search(r"F(\d+(\.\d+)?)", line)
        
        if f_match:
            last_f_used = float(f_match.group(1))
            flow_rate = filament_crossection_area / (last_f_used / 60)  # Flow rate in mm³/s

            min_flow_rate = min(min_flow_rate, flow_rate)
            max_flow_rate = max(max_flow_rate, flow_rate)
    
    # Show max and min flow rates (skipping user confirmation as it requires user input)
    print(f"Max flow rate found: {max_flow_rate} mm³/s")
    print(f"Min flow rate found: {min_flow_rate} mm³/s")

    normalize_by: NormalizeBy | None = None
    while normalize_by != NormalizeBy.MAX and normalize_by != NormalizeBy.MIN:
        normalize_by_input = input(f"Normalize to max or min flow rate? ({NormalizeBy.MAX.value}/{NormalizeBy.MIN.value}): ").upper()
        try:
            normalize_by = NormalizeBy[normalize_by_input]
        except KeyError:
            print("Invalid input. Please try again.")
            continue

    print(f"Will normalize to {normalize_by.value.upper()} flow rate")
    
    while flow_rate_cap == None or flow_rate_cap <= 0 or isinstance(flow_rate_cap, float) == False:
        flow_rate_cap = None
        try:
            flow_rate_cap = float(input(f"Enter new {normalize_by.value.upper()} flow rate in mm³/min: ")) if flow_rate_cap is None else flow_rate_cap
        except ValueError:
            print("The flow rate cap must be a number. Please try again.")
            continue
        if not flow_rate_cap > 0:
            print("The flow rate cap must be > 0. Please try again.")
            continue

    scaling_factor = flow_rate_cap / max_flow_rate if normalize_by == NormalizeBy.MAX else flow_rate_cap / min_flow_rate
    print(f"Scaling factor: {scaling_factor}")

    # Write the modified G-code to a new file
    output_file_path = os.path.splitext(input_file_path)[0] + f"_flow_{flow_rate_cap}_normalized.gcode"
    suffix_number = 0
    last_f_used = None
    while os.path.isfile(output_file_path):
        suffix_number += 1
        output_file_path = os.path.splitext(input_file_path)[0] + f"_flow_{flow_rate_cap}_normalized_{suffix_number}.gcode"

    # Process each line in the G-code file
    for line in original_gcode:
        if not line.startswith(("G0", "G1", "G2", "G3")):
            continue
        
        # Extract F value
        f_match = re.search(r"F(\d+(\.\d+)?)", line)
        
        if f_match:
            last_f_used = float(f_match.group(1))

            # new F value
            new_flow_rate = (filament_crossection_area / (last_f_used / 60)) * scaling_factor  # New flow rate in mm³/s
            new_f_value = (new_flow_rate / filament_crossection_area) * 60  # New F value
            
            # Replace E and F values in the G-code line
            line = re.sub(r"F\d+(\.\d+)?", f"F{new_f_value}", line)
        
        # Append the (potentially modified) line to the modified G-code list
        modified_gcode.append(line)

    with open(output_file_path, 'w') as file:
        file.writelines(modified_gcode)
    print(f"New max flow rate: {max_flow_rate * scaling_factor} mm³/s")
    print(f"New min flow rate: {min_flow_rate * scaling_factor} mm³/s")
    print(f"Normalized G-code has been saved to {output_file_path}.")
    print("Exiting...")

if __name__ == "__main__":
    try:
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
    except KeyboardInterrupt:
        print("Exiting...")
        exit()
