import pandas as pd
import os
from typing import Dict, List, Optional, Tuple, Set
import re
from datetime import datetime
from collections import defaultdict

def load_csv_file(file_path: str) -> pd.DataFrame:
    """
    Load a CSV file from Harzing's Publish or Perish into a pandas DataFrame.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        pd.DataFrame: DataFrame containing the publication data
    """
    try:
        df = pd.read_csv(file_path)
        # Convert Year to numeric, coercing errors to NaN
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        df.attrs['filename'] = file_path.split('/')[-1]
        return df
    except Exception as e:
        print(f"Error loading file {file_path}: {str(e)}")
        return pd.DataFrame()

def save_results(df: pd.DataFrame, filename: str, 
                 output_dir: str = 'csv_results/processed_results') -> str:
    """
    Save a DataFrame to a CSV file in the specified output directory.
    The filename will be prefixed with the current date.
    
    Args:
        df (pd.DataFrame): DataFrame to save
        filename (str): Base name for the file (without .csv extension)
        output_dir (str): Directory to save the file in (default: 'results')
        
    Returns:
        str: Path to the saved file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Add date prefix to filename
    date_prefix = datetime.now().strftime('%Y%m%d')
    full_filename = f"{date_prefix}_{filename}.csv"
    
    # Create full path
    output_path = os.path.join(output_dir, full_filename)
    
    try:
        # Save DataFrame to CSV
        df.to_csv(output_path, index=False)
        print(f"Results saved to {output_path}")
        return output_path
    except Exception as e:
        print(f"Error saving results to {output_path}: {str(e)}")
        return ""

def parse_search_info(filename: str) -> Dict[str, List[str]]:
    """
    Parse the filename to extract search engine and search terms.
    Args:
        filename (str): Name of the CSV file
        
    Returns:
        dict: Dictionary containing search engine and search terms
    """
    # Remove .csv extension
    name = os.path.splitext(filename)[0]
    parts = name.split('_')
    
    search_engine = parts[0]
    terms = []
    excluded = []
    
    i = 1
    while i < len(parts):
        if parts[i] == 'ANDNOT':
            if i + 1 < len(parts):
                excluded.append(parts[i + 1])
                i += 2
        elif parts[i] != 'AND':
            terms.append(parts[i])
            i += 1
        else:
            i += 1
            
    return {
        'search_engine': search_engine,
        'terms': terms,
        'excluded': excluded
    }

def analyze_results(csv_folder: str = 'csv_results') -> Dict[str, Dict]:
    """
    Analyze all CSV files in the specified folder and return statistics.
    
    Args:
        csv_folder (str): Path to folder containing CSV files
        
    Returns:
        dict: Dictionary containing analysis results for each file
    """
    results = {}
    
    for filename in os.listdir(csv_folder):
        if not filename.endswith('.csv'):
            continue
            
        file_path = os.path.join(csv_folder, filename)
        df = load_csv_file(file_path)
        
        if df.empty:
            continue
            
        search_info = parse_search_info(filename)
        
        top_cited = df.nlargest(5, 'Cites')[['Title', 'Authors', 'Year', 'Cites']].to_dict('records')
        # Calculate statistics
        stats = {
            'search_info': search_info,
            'total_papers': len(df),
            'years_range': (df['Year'].min(), df['Year'].max()),
            'total_citations': df['Cites'].sum(),
            'avg_citations': df['Cites'].mean(),
            'top_cited': top_cited
        }
        
        results[filename] = stats
        
    return results

def analyze_results_from_df(df: pd.DataFrame) -> Dict[str, Dict]:
    """
    Analyze a DataFrame and return statistics.
    """
    stats = {
        'search_info': parse_search_info(df.attrs['filename']),
        'total_papers': len(df),
        'years_range': (df['Year'].min(), df['Year'].max()),
        'total_citations': df['Cites'].sum(),
        'avg_citations': df['Cites'].mean(),
        'top_cited': df.nlargest(5, 'Cites')[['Title', 'Authors', 'Year', 'Cites']].to_dict('records')
    }
    return stats


def get_citation_trends(df: pd.DataFrame) -> pd.Series:
    """
    Calculate citation trends by year.
    
    Args:
        df (pd.DataFrame): DataFrame containing publication data
        
    Returns:
        pd.Series: Citations per year
    """
    return df.groupby('Year')['Cites'].sum()

def find_common_papers(dfs: List[pd.DataFrame], threshold: float = 0.8) -> pd.DataFrame:
    """
    Find papers that appear in multiple search results using title similarity.
    
    Args:
        dfs (List[pd.DataFrame]): List of DataFrames to compare
        threshold (float): Similarity threshold for matching titles (0-1)
        
    Returns:
        pd.DataFrame: DataFrame containing papers found in multiple results
    """
    def normalize_title(title: str) -> str:
        return re.sub(r'[^\w\s]', '', title.lower())
    
    common_papers = []
    
    for i, df1 in enumerate(dfs[:-1]):
        for df2 in dfs[i+1:]:
            for _, row1 in df1.iterrows():
                title1 = normalize_title(row1['Title'])
                
                # Find similar titles in df2
                for _, row2 in df2.iterrows():
                    title2 = normalize_title(row2['Title'])
                    
                    # Simple similarity check - can be improved with better algorithms
                    if len(title1) > 0 and len(title2) > 0:
                        similarity = len(set(title1.split()) & set(title2.split())) / len(set(title1.split()))
                        
                        if similarity >= threshold:
                            common_papers.append({
                                'Title': row1['Title'],
                                'Authors': row1['Authors'],
                                'Year': row1['Year'],
                                'Cites': row1['Cites']
                            })
                            break
                            
    return pd.DataFrame(common_papers).drop_duplicates()

if __name__ == "__main__":
    # Example usage
    results = analyze_results()
    
    for filename, stats in results.items():
        print(f"\nAnalysis for {filename}:")
        print(f"Search engine: {stats['search_info']['search_engine']}")
        print(f"Search terms: {stats['search_info']['terms']}")
        print(f"Excluded terms: {stats['search_info']['excluded']}")
        print(f"Total papers: {stats['total_papers']}")
        print(f"Years range: {stats['years_range']}")
        print(f"Total citations: {stats['total_citations']}")
        print(f"Average citations: {stats['avg_citations']:.2f}")
        print("\nTop 5 cited papers:")
        for paper in stats['top_cited']:
            print(f"- {paper['Title']} ({paper['Year']}) - {paper['Cites']} citations") 