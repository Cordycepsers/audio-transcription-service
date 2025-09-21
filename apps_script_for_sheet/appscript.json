# Transcript Analysis Tool

## Overview
This Google Apps Script tool automatically processes transcript data in a Google Sheets document to extract key information such as years mentioned and foundation-related keywords. The script analyzes "Introduce Yourself" transcripts and populates designated columns with structured data for further analysis.

## Configuration
The script uses a configuration object to map important columns:

```javascript
const CONFIG = {
  SOURCE_COL: 8,        // Column G ("Introduce Yourself TRANSCRIPT")
  YEAR_TARGET_COL: 17,  // Column U ("YEARS AT FOUNDATION")
  KEYWORD_TARGET_COL: 18 // Column V ("FOUNDATION TEAMS AI")
};
```

## Features

### Configuration Validation
The script includes a validation function to ensure column indices are properly configured:

```javascript
function validateConfig() {
  const minCol = 1;
  const maxCol = 26; // Assuming a maximum of 26 columns (A-Z)
  return (
    CONFIG.SOURCE_COL >= minCol && CONFIG.SOURCE_COL <= maxCol &&
    CONFIG.YEAR_TARGET_COL >= minCol && CONFIG.YEAR_TARGET_COL <= maxCol &&
    CONFIG.KEYWORD_TARGET_COL >= minCol && CONFIG.KEYWORD_TARGET_COL <= maxCol
  );
}
```

### Year Extraction
The tool extracts years within the range 1900-2030 from transcript text, handling various formats:

```javascript
function extractYears(text) {
  if (!text) return '';
  
  // Array to store all found years
  let foundYears = [];
  
  // Handle standard year formats (1999-2030)
  const standardYearRegex = /\b(19\d{2}|20[0-2]\d|2030)\b/g;
  const standardYears = [...text.matchAll(standardYearRegex)].map(match => parseInt(match[0]));
  foundYears.push(...standardYears);
  
  // Additional year extraction logic...
}
```

## Usage
1. Configure the column mappings in the CONFIG object to match your spreadsheet structure
2. Run the script to process transcript data
3. Review the extracted years and keywords in the designated columns

## Requirements
- Google Sheets document with transcript data
- Google Apps Script editor access

## Note
This script is designed to work with specific spreadsheet structures. Adjust the configuration as needed for your particular use case.