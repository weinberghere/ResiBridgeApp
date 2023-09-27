import csv

def exclude_csv_columns(input_file, output_file, exclude_columns):
    """
    Exclude specific columns from a CSV.

    Parameters:
    - input_file (str): Path to the input CSV file.
    - output_file (str): Path to the output CSV file.
    - exclude_columns (list): List of column names to exclude.
    """
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = [field for field in reader.fieldnames if field not in exclude_columns]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in reader:
            writer.writerow({field: row[field] for field in fieldnames})
