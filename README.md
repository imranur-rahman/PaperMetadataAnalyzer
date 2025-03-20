# top4grep
A tool for searching papers from top security and software engineering conferences

## Installation
```bash
git clone https://github.com/Kyle-Kyle/top4grep
cd top4grep
pip3 install -e .
```

## Usage 
### Database Initialization
Build the paper database with optional conference type selection or update the database of papers stored in `papers.db`:

```bash
# Build database for all conferences (default)
top4grep --build-db

# Build database for security conferences only
top4grep --build-db --conference-type security

# Build database for software engineering conferences only
top4grep --build-db --conference-type software_engineering
```

Supported conferences:
- Security: NDSS, IEEE S&P, USENIX, CCS
- Software Engineering: ICSE, FSE, ASE, ISSTA

### Query
```bash
top4grep -k <keywords> [--start-year YEAR]
```

Examples:
```bash
# Search for papers with keywords from all years (default: 2000)
top4grep -k linux,kernel

# Search for papers from 2015 onwards
top4grep -k linux,kernel --start-year 2015
```

The query performs a case-insensitive match (like grep). The returned results must contain all input keywords (papers containing keyword1 AND keyword2 AND ...). Support for `OR` operation (papers containing keyword1 OR keyword2) is planned for future updates.

## Screenshot
![screenshot](https://raw.githubusercontent.com/Kyle-Kyle/top4grep/master/img/screenshot.png)

## TODO
- [ ] grep in abstract
- [ ] fuzzy match
- [ ] complex search logic (`OR` operation)
