from typing import Dict, List, Optional, Set
import requests
import time
import random
import re
from bs4 import BeautifulSoup
import os

def get_citation_count_from_doi(doi: str) -> Optional[Dict]:
    """
    Retrieve metadata for an article using its DOI via the Semantic Scholar API.
    
    Args:
        doi (str): The DOI of the article
        
    Returns:
        Optional[Dict]: Dictionary containing paper metadata including citation count,
                       or None if not found or error occurs
    """
    # Remove any URL prefix if present
    doi = str(doi).replace('https://doi.org/', '')
    
    # Semantic Scholar API endpoint
    url = f'https://api.semanticscholar.org/v1/paper/{doi}'
    
    try:
        # Add a small delay to respect rate limits
        time.sleep(0.1)
        
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()
        
        # Extract relevant information
        result = {
            'doi': doi,
            'title': data.get('title', ''),
            'year': data.get('year'),
            'citationCount': data.get('citationCount', 0),
            'influentialCitationCount': data.get('influentialCitationCount', 0),
            'venue': data.get('venue', ''),
            'authors': [author.get('name', '') for author in data.get('authors', [])],
            'abstract': data.get('abstract', ''),
            'url': data.get('url', ''),
            'isOpenAccess': data.get('isOpenAccess', False)
        }
        
        if not result['title']:
            print(f"No paper found for DOI: {doi}")
            return None
            
        return result
            
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving data for DOI {doi}: {str(e)}")
        return None

def get_citation_count_from_google_scholar(doi: str) -> Optional[int]:
    """
    Get citation count from Google Scholar using web scraping.
    Note: This is not recommended for large-scale use as it may get blocked.
    
    Args:
        doi (str): The DOI of the article
        
    Returns:
        Optional[int]: Citation count if found, None otherwise
    """
    # Clean DOI
    doi = str(doi).strip()
    doi = doi.replace('https://doi.org/', '')
    doi = doi.replace('http://doi.org/', '')
    
    # Construct Google Scholar search URL
    search_url = f'https://scholar.google.com/scholar?q=doi:{doi}'
    
    try:
        # Add random delay between 2-5 seconds to avoid getting blocked
        time.sleep(random.uniform(2, 5))
        
        # Use a browser-like user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the citation count
        # Google Scholar shows citations in the format "Cited by X"
        citation_text = soup.find(text=re.compile(r'Cited by \d+'))
        if citation_text:
            # Extract the number from "Cited by X"
            citation_count = int(re.search(r'Cited by (\d+)', citation_text).group(1))
            return citation_count
            
        return 0  # Return 0 if no citations found
            
    except Exception as e:
        print(f"Google Scholar error for DOI {doi}: {str(e)}")
        return None

def get_citation_count_from_multiple_sources(doi: str) -> Optional[Dict]:
    """
    Try to get citation count from multiple sources in sequence.
    Currently supports:
    - Semantic Scholar
    - CrossRef
    - Scopus (if API key is provided)
    - Google Scholar (as last resort)
    
    Args:
        doi (str): The DOI of the article
        
    Returns:
        Optional[Dict]: Dictionary containing paper metadata including citation count,
                       or None if not found or error occurs
    """
    # Clean and normalize DOI
    doi = str(doi).strip()
    doi = doi.replace('https://doi.org/', '')
    doi = doi.replace('http://doi.org/', '')
    
    # Try Semantic Scholar first
    result = get_citation_count_from_doi(doi)
    if result:
        if result['citationCount'] > 0:
            return result['citationCount']
        
    # Try CrossRef
    try:
        url = f'https://api.crossref.org/works/{doi}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if 'message' in data:
            result = {
                'doi': doi,
                'title': data['message'].get('title', [''])[0],
                'year': data['message'].get('published-print', {}).get('date-parts', [[None]])[0][0],
                'citationCount': data['message'].get('is-referenced-by-count', 0),
                'venue': data['message'].get('container-title', [''])[0],
                'authors': [author.get('given', '') + ' ' + author.get('family', '') 
                          for author in data['message'].get('author', [])],
                'url': data['message'].get('URL', ''),
                'isOpenAccess': data['message'].get('is-referenced-by-count', 0) > 0
            }
            
            if result['citationCount'] > 0:
                return result['citationCount']
                
    except Exception as e:
        print(f"CrossRef API error: {str(e)}")
    
    # Try Scopus if API key is available
    scopus_api_key = os.getenv('SCOPUS_API_KEY')
    if scopus_api_key:
        try:
            url = f'https://api.elsevier.com/content/article/doi/{doi}'
            headers = {'X-ELS-APIKey': scopus_api_key}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if 'full-text-retrieval-response' in data:
                result = {
                    'doi': doi,
                    'title': data['full-text-retrieval-response'].get('coredata', {}).get('dc:title', ''),
                    'year': data['full-text-retrieval-response'].get('coredata', {}).get('prism:coverDate', '')[:4],
                    'citationCount': data['full-text-retrieval-response'].get('coredata', {}).get('citedby-count', 0),
                    'venue': data['full-text-retrieval-response'].get('coredata', {}).get('prism:publicationName', ''),
                    'authors': [author.get('given-name', '') + ' ' + author.get('surname', '')
                              for author in data['full-text-retrieval-response'].get('authors', {}).get('author', [])],
                    'url': data['full-text-retrieval-response'].get('coredata', {}).get('link', [{}])[0].get('@href', ''),
                    'isOpenAccess': data['full-text-retrieval-response'].get('coredata', {}).get('openaccess', 0) == 1
                }
                
                if result['citationCount'] > 0:
                    return result['citationCount']
                    
        except Exception as e:
            print(f"Scopus API error: {str(e)}")
    
    # Try Google Scholar as last resort
    print(f"Trying Google Scholar for DOI: {doi}")
    citation_count = get_citation_count_from_google_scholar(doi)
    if citation_count is not None:
        return citation_count
    
    # If we get here, we couldn't find any data
    print(f"Could not find citation data for DOI: {doi}")
    return 0  # Return 0 instead of None to indicate we tried but found no citations


def fill_acm_citation_count(csv_file_path: str) -> pd.DataFrame:
    """
    Fill the citation count for ACM papers in a CSV file.
    """
    df = pd.read_csv(csv_file_path)
    total = len(df)
    updated = 0
    
    print(f"Processing {total} papers...")
    
    for index, row in df.iterrows():
        if pd.isna(row['DOI']):
            continue

        if row['Cites'] > 0:
            continue
            
        doi = row['DOI']
        citation_count = get_citation_count_from_multiple_sources(doi)
        
        if citation_count is not None:
            df.at[index, 'Cites'] = citation_count
            updated += 1
            
            # Save progress every 10 papers
            if updated % 10 == 0:
                df.to_csv(csv_file_path, index=False)
                print(f"Progress: {updated}/{total} papers processed")
                
    # Final save
    df.to_csv(csv_file_path, index=False)
    print(f"\nCompleted! Updated {updated} out of {total} papers")
    return df
