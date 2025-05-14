import os
import re
import sqlite3

def find_sql_queries():
    """Find all SQL queries in the codebase that reference horario_clase"""
    queries = []
    files_with_queries = []
    
    # Walk through all Python files in the project
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # Skip virtualenv files
                if 'venv' in file_path:
                    continue
                    
                # Read file content
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Look for SQL queries that reference horario_clase
                    if 'horario_clase' in content and 'SELECT' in content:
                        # Extract SQL queries using regex pattern matching
                        # This is a simple approach and might miss some complex queries
                        sql_patterns = [
                            r'SELECT.*?FROM\s+horario_clase\s+.*?(?:;|"""|\'\'\'))',
                            r'SELECT.*?FROM\s+horario_clase\s+WHERE.*?(?:;|"""|\'\'\'))',
                            r'HorarioClase\.query\.filter.*?\)',
                            r'HorarioClase\.query\.filter_by.*?\)',
                            r'conn\.execute\([\'"]SELECT.*?FROM\s+horario_clase.*?[\'"]\)',
                            r'cursor\.execute\([\'"]SELECT.*?FROM\s+horario_clase.*?[\'"]\)'
                        ]
                        
                        for pattern in sql_patterns:
                            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                            if matches:
                                for match in matches:
                                    queries.append((file_path, match.strip()))
                                
                                if file_path not in files_with_queries:
                                    files_with_queries.append(file_path)
                except Exception as e:
                    print(f"Error reading {file_path}: {str(e)}")
    
    return queries, files_with_queries

def check_activo_filter(queries):
    """Check if queries include activo=1 or activo=True filter"""
    missing_filter = []
    
    for file_path, query in queries:
        # Skip pure SELECT COUNT queries which are usually for stats
        if re.search(r'SELECT\s+COUNT\(', query, re.IGNORECASE):
            continue
            
        # Check for activo filter in various forms
        has_activo_filter = any([
            'activo = 1' in query.lower(),
            'activo=1' in query.lower(),
            'activo=true' in query.lower(),
            'activo = true' in query.lower(),
            'activo=True' in query,
            'activo = True' in query,
            'WHERE activo' in query,
            'filter_by(activo=' in query,
            'filter(HorarioClase.activo ==' in query,
            'filter(HorarioClase.activo' in query
        ])
        
        # Record queries missing the filter
        if not has_activo_filter and not any([
            # Exclude queries that are clearly not for listing active classes
            'UPDATE horario_clase SET' in query,
            'INSERT INTO horario_clase' in query,
            'DELETE FROM horario_clase' in query
        ]):
            missing_filter.append((file_path, query))
    
    return missing_filter

def print_results(queries, files_with_queries, missing_filter):
    """Print analysis results"""
    print(f"Found {len(queries)} SQL queries referencing horario_clase in {len(files_with_queries)} files")
    print("\nFiles with horario_clase queries:")
    for file_path in files_with_queries:
        print(f"  - {file_path}")
    
    print(f"\nFound {len(missing_filter)} queries that may be missing activo filter:")
    for i, (file_path, query) in enumerate(missing_filter):
        print(f"\n{i+1}. {file_path}:")
        
        # Print a shorter version of the query to avoid too much output
        short_query = query[:200] + "..." if len(query) > 200 else query
        print(f"   {short_query}")
    
    print("\nRecommendation:")
    print("  Review the listed queries and consider adding 'activo=1' or equivalent filter")
    print("  For ORM queries: HorarioClase.query.filter_by(activo=True)")
    print("  For SQL queries: WHERE activo = 1")

if __name__ == "__main__":
    print("Analyzing SQL queries for horario_clase filtering...\n")
    
    queries, files_with_queries = find_sql_queries()
    missing_filter = check_activo_filter(queries)
    print_results(queries, files_with_queries, missing_filter) 