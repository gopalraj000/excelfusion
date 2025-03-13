import pandas as pd
from typing import List, Dict, Tuple, Set
import io

def read_file(uploaded_file) -> pd.DataFrame:
    """Read uploaded Excel/CSV file into pandas DataFrame."""
    try:
        if uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xls', '.xlsx')):
            return pd.read_excel(uploaded_file)
        else:
            raise ValueError("Unsupported file format")
    except Exception as e:
        raise ValueError(f"Error reading file: {str(e)}")

def merge_dataframes(dfs: List[pd.DataFrame], merge_columns: Dict[str, str], selected_columns: Dict[str, Set[str]], df_names: List[str], merge_type: str = 'outer') -> Tuple[pd.DataFrame, Dict]:
    """Merge multiple DataFrames based on specified column mappings."""
    if not dfs or len(dfs) < 2:
        raise ValueError("At least two DataFrames are required for merging")

    # Filter DataFrames to keep only selected columns and rename for clarity
    filtered_dfs = []
    for i, (df, name) in enumerate(zip(dfs, df_names)):
        # Always include the merge column
        merge_col = merge_columns[f"df{i}"]
        selected_cols = selected_columns.get(f"df{i}", set())

        # Ensure merge column is included even if not selected
        cols_to_keep = list(selected_cols | {merge_col})

        # Create a copy of the DataFrame with selected columns
        filtered_df = df[cols_to_keep].copy()

        # Rename columns to include file name (except merge column)
        rename_dict = {
            col: f"{name.split('.')[0]}_{col}" 
            for col in filtered_df.columns 
            if col != merge_col
        }
        filtered_df.rename(columns=rename_dict, inplace=True)
        filtered_dfs.append(filtered_df)

    result = filtered_dfs[0]
    merge_stats = {
        'total_rows_original': sum(len(df) for df in dfs),
        'new_rows_per_file': {},
        'missing_rows_per_file': {}
    }

    for i, df in enumerate(filtered_dfs[1:], 1):
        left_col = merge_columns[f"df0"]
        right_col = merge_columns[f"df{i}"]

        try:
            # Count unique values before merge
            left_keys = set(result[left_col])
            right_keys = set(df[right_col])

            # Calculate new and missing rows
            new_rows = len(right_keys - left_keys)
            missing_rows = len(left_keys - right_keys)

            merge_stats['new_rows_per_file'][i] = new_rows
            merge_stats['missing_rows_per_file'][i] = missing_rows

            # Perform merge
            result = result.merge(
                df,
                left_on=left_col,
                right_on=right_col,
                how=merge_type
            )

            # If merge columns have different names, drop the duplicate
            if left_col != right_col:
                result = result.drop(right_col, axis=1)

        except Exception as e:
            raise ValueError(f"Error merging DataFrames: {str(e)}")

    merge_stats['total_rows_merged'] = len(result)
    return result, merge_stats

def get_download_buffer(df: pd.DataFrame, file_format: str) -> Tuple[io.BytesIO, str]:
    """Prepare DataFrame for download in specified format."""
    buffer = io.BytesIO()

    if file_format == 'csv':
        df.to_csv(buffer, index=False)
        mime = 'text/csv'
    else:  # Excel
        df.to_excel(buffer, index=False)
        mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    buffer.seek(0)
    return buffer, mime