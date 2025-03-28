import pandas as pd
import bibtexparser
import os
from datetime import datetime

def convert_ieee_to_standard_format(file_path: str) -> pd.DataFrame:
    """
    Convert IEEE CSV format to the standard format used by other files.
    
    Args:
        file_path (str): Path to the IEEE CSV file
        
    Returns:
        pd.DataFrame: DataFrame in the standard format
    """
    # Read the IEEE CSV file
    df = pd.read_csv(file_path)
    
    # Create a new DataFrame with the standard columns
    standard_df = pd.DataFrame()
    
    # Map the columns
    standard_df['Title'] = df['Document Title']
    standard_df['Authors'] = df['Authors']
    standard_df['Year'] = pd.to_numeric(df['Publication Year'], errors='coerce')
    standard_df['Cites'] = pd.to_numeric(df['Article Citation Count'], errors='coerce').fillna(0)
    
    # Add any additional columns that might be useful
    standard_df['Abstract'] = df['Abstract']
    standard_df['DOI'] = df['DOI']
    standard_df['Journal'] = df['Publication Title']
    
    # Store the original filename as an attribute
    standard_df.attrs['filename'] = os.path.basename(file_path)
    
    return standard_df

def convert_bib_to_csv(bib_file_path: str, output_dir: str = 'csv_results/HPP_results') -> str:
    """
    Convert a BibTeX file to CSV format matching the structure of other CSV files.
    
    Args:
        bib_file_path (str): Path to the BibTeX file
        output_dir (str): Directory to save the CSV file (default: 'csv_results/HPP_results')
        
    Returns:
        str: Path to the saved CSV file
    """
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Read the BibTeX file
        with open(bib_file_path, 'r', encoding='utf-8') as bibtex_file:
            bib_database = bibtexparser.load(bibtex_file)
        
        # Create a DataFrame from the BibTeX entries
        df = pd.DataFrame(bib_database.entries)
        
        # Map BibTeX fields to our standard format
        standard_df = pd.DataFrame()
        
        # Required fields
        standard_df['Title'] = df['title'].fillna('')
        standard_df['Authors'] = df['author'].fillna('')
        standard_df['Year'] = pd.to_numeric(df['year'], errors='coerce')
        standard_df['Cites'] = 0  # Citation count is not available in BibTeX
        
        # Optional fields that might be useful
        standard_df['Abstract'] = df.get('abstract', '').fillna('')
        standard_df['DOI'] = df.get('doi', '').fillna('')
        standard_df['Journal'] = df.get('journal', '').fillna('')
        
        # Store the original filename as an attribute
        standard_df.attrs['filename'] = os.path.basename(bib_file_path)
        
        # Generate output filename
        date_prefix = datetime.now().strftime('%Y%m%d')
        output_filename = f"{date_prefix}_bibtex_{os.path.splitext(os.path.basename(bib_file_path))[0]}.csv"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save to CSV
        standard_df.to_csv(output_path, index=False)
        print(f"Converted BibTeX file saved to {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error converting BibTeX file {bib_file_path}: {str(e)}")
        return ""