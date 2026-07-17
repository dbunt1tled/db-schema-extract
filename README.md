# DB Structure Extract

A Python tool for extracting and visualizing MySQL database schemas as diagrams. Connects to multiple databases, introspects their structure (tables, columns, primary/foreign keys), and renders professional entity-relationship diagrams using Graphviz.

## Features

- **Multi-database support**: Process multiple MySQL databases in a single run
- **Flexible schema introspection**: Extract tables, columns, data types, and constraints
- **Multiple output formats**: PNG, SVG, JPEG
- **Layout options**: dot (hierarchical), grid (tabular), neato, fdp, sfdp, osage (force-directed)
- **Split modes**: Generate single diagram, split by schema, or split by connected components
- **Foreign key visualization**: Optional relationship lines between tables
- **Color-coded elements**: Primary keys (yellow), foreign keys (blue), headers (dark)
- **Async processing**: Efficient concurrent database connections using SQLAlchemy async

## Requirements

- Python 3.14+
- MySQL database with async driver support
- Graphviz installed on your system

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd db_struct_extract
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Install Graphviz (system dependency):
- **macOS**: `brew install graphviz`
- **Ubuntu/Debian**: `sudo apt-get install graphviz`
- **Windows**: Download from [graphviz.org](https://graphviz.org/download/)

## Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` with your database connections and settings:

```env
# Output settings
EXPORT_FORMAT=png          # png, svg, jpeg
DPI=96                     # Resolution for raster formats
SPLIT=none                 # none, schema, components
SHOW_RELATIONS=false       # Show foreign key relationships
OUTPUT_DIR=output          # Output directory
BIG_THRESHOLD=60           # Warning threshold for large databases

# Layout settings
LAYOUT=grid                # dot, grid, neato, fdp, sfdp, osage
GRID_COLUMNS=40            # Columns for grid layout

# Database connections (add multiple DB_1_, DB_2_, etc.)
DB_1_NAME=my_database
DB_1_SCHEMA=my_schema
DB_1_URL=mysql+aiomysql://user:password@localhost:3306/my_database
```

### Configuration Options

- **EXPORT_FORMAT**: Output image format (`png`, `svg`, `jpeg`)
- **DPI**: Resolution in dots per inch (48-600, default: 96)
- **SPLIT**: How to split diagrams (`none`, `schema`, `components`)
- **SHOW_RELATIONS**: Draw lines between tables with foreign key relationships
- **OUTPUT_DIR**: Directory for generated diagrams
- **BIG_THRESHOLD**: Table count threshold for large database warnings
- **LAYOUT**: Graphviz layout algorithm
  - `dot`: Hierarchical layout (good for showing relationships)
  - `grid`: Grid layout with specified columns (good for few relationships)
  - `neato/fdp/sfdp/osage`: Force-directed 2D layouts (compact)
- **GRID_COLUMNS**: Number of columns when using grid layout

### Database Connection Format

Each database requires three variables:
- `DB_<N>_NAME`: Display name for the database
- `DB_<N>_SCHEMA`: Schema name(s) to introspect (comma-separated, or `*` for all)
- `DB_<N>_URL`: SQLAlchemy async connection string

Supported URL formats:
- `mysql+aiomysql://user:password@host:port/database`
- `mysql+asyncmy://user:password@host:port/database`

## Usage

Run the tool with the default `.env` file:

```bash
python main.py
```

Specify a custom environment file:

```bash
python main.py --env /path/to/custom.env
```

## Examples

### Single Database, Simple Diagram
```env
EXPORT_FORMAT=svg
SHOW_RELATIONS=true
LAYOUT=dot
DB_1_NAME=production
DB_1_SCHEMA=public
DB_1_URL=mysql+aiomysql://user:pass@localhost:3306/production
```

### Multiple Databases, Grid Layout
```env
EXPORT_FORMAT=png
LAYOUT=grid
GRID_COLUMNS=6
SHOW_RELATIONS=false
DB_1_NAME=users_db
DB_1_SCHEMA=users
DB_1_URL=mysql+aiomysql://user:pass@localhost:3306/users_db
DB_2_NAME=orders_db
DB_2_SCHEMA=orders
DB_2_URL=mysql+aiomysql://user:pass@localhost:3306/orders_db
```

### Large Database, Split by Components
```env
EXPORT_FORMAT=svg
SPLIT=components
SHOW_RELATIONS=true
LAYOUT=dot
DB_1_NAME=large_db
DB_1_SCHEMA=*
DB_1_URL=mysql+aiomysql://user:pass@localhost:3306/large_db
```

## Output

Diagrams are saved to the `OUTPUT_DIR` with filenames based on database names:
- Single diagram: `{DB_NAME}.svg`
- Split by schema: `{DB_NAME}__{SCHEMA_NAME}.svg`
- Split by components: `{DB_NAME}__part01.svg`, `{DB_NAME}__part02.svg`, etc.

## Development

The project uses:
- **uv**: Package management
- **ruff**: Linting and formatting
- **mypy**: Type checking
- **isort**: Import sorting

Run linting:
```bash
uv run ruff check .
uv run ruff format .
```

Run type checking:
```bash
uv run mypy .
```

## Project Structure

```
db_struct_extract/
├── main.py                 # CLI entry point
├── src/
│   ├── config/
│   │   └── settings.py     # Configuration management
│   ├── db/
│   │   └── introspect.py   # Database schema introspection
│   └── render/
│       └── render.py       # Graphviz diagram rendering
├── .env.example            # Configuration template
└── pyproject.toml          # Project dependencies
```

## License

[Specify your license here]
