# Product Context: NewsNewt

## Product Vision

NewsNewt is a self-hosted web scraping microservice that empowers n8n users to extract structured data from web pages without complex setup or maintenance.

## Target Users

### Primary Users
- **n8n Workflow Builders**: Users creating automation workflows in n8n
- **Data Collectors**: Users needing to extract data from websites regularly
- **Content Aggregators**: Users building content aggregation systems

### User Personas

#### Persona 1: Automation Engineer
- **Needs**: Reliable scraping for workflow automation
- **Pain Points**: Complex scraping tools, CAPTCHA issues, unreliable extraction
- **Value**: Simple API, automatic popup handling, CAPTCHA detection

#### Persona 2: Content Manager
- **Needs**: Extract article content, titles, authors, dates
- **Pain Points**: Manual copying, inconsistent formats
- **Value**: Automatic extraction with fallbacks, structured JSON output

## Use Cases

### Use Case 1: News Article Extraction
- **Scenario**: Extract article content from news websites
- **Input**: URL + selectors for title, content, author, date
- **Output**: Structured JSON with extracted fields
- **Integration**: n8n HTTP Request node → Store in database

### Use Case 2: Product Information Scraping
- **Scenario**: Monitor product prices and details
- **Input**: Product URLs + selectors for price, title, description
- **Output**: JSON with product data
- **Integration**: Scheduled n8n workflow → Price alerts

### Use Case 3: Content Aggregation
- **Scenario**: Aggregate content from multiple sources
- **Input**: List of URLs with common selectors
- **Output**: Consistent JSON format across sources
- **Integration**: Loop in n8n → Normalize → Store

## Value Propositions

1. **Simplicity**: Single Docker container, minimal configuration
2. **Reliability**: Structured error handling, automatic retries
3. **Intelligence**: Automatic popup dismissal, CAPTCHA detection, fallback extraction
4. **Integration**: Designed specifically for n8n workflows
5. **Self-Hosted**: Full control, no external dependencies

## User Experience Goals

### For n8n Users
- **Easy Setup**: `docker compose up` and it works
- **Clear Errors**: Structured error responses with actionable messages
- **Fast Response**: Target <3-5 seconds per scrape
- **Reliable**: Handles common web patterns automatically

### For Developers
- **Maintainable**: Clean code, clear structure
- **Observable**: Comprehensive logging, health checks
- **Extensible**: Easy to add new extraction strategies

## Success Metrics

- **Reliability**: >95% successful scrapes (excluding CAPTCHA/timeout)
- **Performance**: Average scrape time <5 seconds
- **Usability**: Setup time <5 minutes
- **Maintainability**: Code quality scores, test coverage

## Competitive Advantages

1. **n8n Optimized**: Designed specifically for n8n integration
2. **Self-Hosted**: No external API dependencies
3. **Intelligent**: Automatic handling of common web patterns
4. **Simple**: Minimal configuration, clear API
5. **Reliable**: Structured error handling, comprehensive logging

## Future Enhancements (Not in Current Scope)

- Multi-page crawling support
- Authentication handling
- Rate limiting
- API key authentication
- Proxy support
- Custom extraction strategies via plugins
