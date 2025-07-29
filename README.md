# Credit History Processor

A comprehensive Python tool for extracting and analyzing credit history information from PDF documents using AI-powered text extraction and parameter identification.

## Features

- **PDF Text Extraction**: Extracts paragraphs from credit history PDFs using regex patterns
- **AI-Powered Analysis**: Uses Mistral AI to identify loan parameters from extracted text
- **Structured Data Storage**: SQLite database for efficient data management
- **CSV Export**: Exports processed data for analysis
- **Batch Processing**: Handles large documents with configurable batch sizes
- **Error Handling**: Robust error handling with detailed logging
- **Progress Tracking**: Real-time progress updates for long-running operations

## Installation

1. **Clone or download the files**:
   ```bash
   git clone <repository-url>
   cd creditstory
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   export MISTRAL_API_KEY="your_mistral_api_key_here"
   ```

## Configuration

The script uses environment variables for configuration. Key settings:

- `MISTRAL_API_KEY`: Your Mistral AI API key (required)
- `BATCH_SIZE`: Number of paragraphs to process in each batch (default: 5)
- `API_DELAY`: Delay between API calls in seconds (default: 1.0)
- `CREDIT_DB_PATH`: Database file path (default: credit_history.db)

## Usage

### Basic Usage

```bash
python credit_history_processor.py <pdf_file> <start_page> <end_page> [output_csv]
```

### Examples

1. **Process pages 1-100**:
   ```bash
   python credit_history_processor.py ./data/credit_history.pdf 1 100
   ```

2. **Process specific page range with custom output**:
   ```bash
   python credit_history_processor.py ./data/credit_history.pdf 50 200 my_loans.csv
   ```

3. **Process large document in chunks**:
   ```bash
   # First batch
   python credit_history_processor.py ./data/credit_history.pdf 1 500 batch1.csv
   
   # Second batch
   python credit_history_processor.py ./data/credit_history.pdf 501 1000 batch2.csv
   ```

## Output Files

### 1. Database (`credit_history.db`)
SQLite database containing:
- **paragraphs table**: Raw extracted paragraphs with processing status
- **loans table**: Structured loan information extracted by AI

### 2. CSV File
Exported loan data with columns:
- `id`: Unique loan identifier
- `paragraph_id`: Source paragraph ID
- `page_number`: PDF page number
- `bank_name`: Bank or credit institution name
- `deal_date`: Loan agreement date
- `deal_type`: Type of loan agreement
- `loan_type`: Category of loan
- `card_usage`: Whether payment card is used
- `loan_amount`: Principal amount
- `loan_currency`: Currency code
- `termination_date`: Loan termination date
- `loan_status`: Current status (Active/Closed)
- `extracted_at`: Processing timestamp

### 3. Log File (`credit_processor.log`)
Detailed processing logs including:
- Extraction progress
- AI processing results
- Error messages
- Statistics

## Processing Workflow

1. **PDF Extraction**: 
   - Reads PDF pages using PyPDF2
   - Filters out headers/footers
   - Extracts paragraphs using regex patterns
   - Stores in SQLite database

2. **AI Processing**:
   - Processes paragraphs in batches
   - Sends each paragraph to Mistral AI
   - Extracts structured loan parameters
   - Validates data using Pydantic models

3. **Data Export**:
   - Exports processed loans to CSV
   - Generates processing statistics
   - Provides success/error rates

## Performance Considerations

### For Large Documents (1500+ pages, 200+ paragraphs):

1. **Batch Processing**: Process in smaller chunks (e.g., 100-200 pages at a time)
2. **API Rate Limiting**: Use conservative delays (1-2 seconds between calls)
3. **Memory Management**: The script processes pages sequentially to manage memory
4. **Resume Capability**: Can restart processing from where it left off

### Recommended Settings for Large Documents:

```bash
export BATCH_SIZE=3
export API_DELAY=2.0
```

## Error Handling

The script handles various error scenarios:

- **PDF Reading Errors**: Continues processing other pages
- **AI API Errors**: Logs errors and continues with next paragraph
- **Data Validation Errors**: Marks paragraphs with errors for review
- **Network Issues**: Implements retry logic for API calls

## Troubleshooting

### Common Issues:

1. **No paragraphs extracted**:
   - Check PDF content and page range
   - Verify regex patterns match document format
   - Review log file for extraction details

2. **API errors**:
   - Verify MISTRAL_API_KEY is set correctly
   - Check API quota and rate limits
   - Increase API_DELAY if hitting rate limits

3. **Memory issues**:
   - Process smaller page ranges
   - Monitor system memory usage
   - Consider using SSD storage for database

### Debug Mode:

Set log level to DEBUG for detailed information:
```bash
export LOG_LEVEL=DEBUG
```

## Data Analysis

The exported CSV file can be used for:

- **Loan Portfolio Analysis**: Distribution of loan types and amounts
- **Bank Analysis**: Most common lenders and their terms
- **Temporal Analysis**: Loan activity over time
- **Risk Assessment**: Analysis of loan statuses and amounts

## Contributing

To improve the script:

1. **Add new regex patterns** in `config.py` for different document formats
2. **Enhance AI prompts** for better parameter extraction
3. **Add new loan parameters** to the `Loan` model
4. **Implement additional export formats** (JSON, Excel, etc.)

## License

This project is provided as-is for educational and research purposes.
