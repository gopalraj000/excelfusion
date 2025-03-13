import streamlit as st
import pandas as pd
from utils import read_file, merge_dataframes, get_download_buffer

def main():
    st.set_page_config(
        page_title="Excel/CSV Merger",
        page_icon="📊",
        layout="wide"
    )

    st.title("📊 Excel/CSV Merger Tool")
    st.write("Upload multiple Excel or CSV files and merge them based on common columns")

    # File upload section with improved feedback
    st.header("1. Upload Files")
    with st.expander("📌 Supported File Types", expanded=False):
        st.write("""
        - CSV files (.csv)
        - Excel files (.xlsx, .xls)
        """)

    uploaded_files = st.file_uploader(
        "Choose Excel/CSV files",
        type=['csv', 'xlsx', 'xls'],
        accept_multiple_files=True,
        help="Upload two or more files to merge"
    )

    if not uploaded_files or len(uploaded_files) < 2:
        st.warning("⚠️ Please upload at least two files to merge")
        st.stop()

    # Read and store DataFrames with progress
    dfs = []
    df_names = []
    with st.spinner("Processing uploaded files..."):
        try:
            for file in uploaded_files:
                df = read_file(file)
                dfs.append(df)
                df_names.append(file.name)
                st.success(f"✅ Successfully loaded: {file.name} ({len(df)} rows, {len(df.columns)} columns)")
        except ValueError as e:
            st.error(f"❌ Error: {str(e)}")
            st.stop()

    # Column selection section
    st.header("2. Select Columns")
    st.info("🔍 Choose which columns to include in the final merged file")

    selected_columns = {}

    # Create tabs for each file
    tabs = st.tabs([f"📄 {name}" for name in df_names])

    # Display column selection for each DataFrame
    for i, (df, tab, name) in enumerate(zip(dfs, tabs, df_names)):
        with tab:
            st.caption(f"Select columns from {name}")
            all_cols = df.columns.tolist()

            # Add select/deselect all buttons
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button(f"Select All", key=f"select_all_{i}"):
                    selected_columns[f"df{i}"] = set(all_cols)
            with col2:
                if st.button(f"Deselect All", key=f"deselect_all_{i}"):
                    selected_columns[f"df{i}"] = set()

            # Column checkboxes in a container for better organization
            with st.container():
                selected = st.multiselect(
                    "Choose columns to include:",
                    options=all_cols,
                    default=all_cols,
                    key=f"cols_{i}",
                    help="Select the columns you want to include in the merged file"
                )
                selected_columns[f"df{i}"] = set(selected)

    # Column mapping section
    st.header("3. Column Mapping")
    st.info("🔍 Select the columns to use as keys for merging the files")

    merge_columns = {}

    # Create columns for each DataFrame
    cols = st.columns(len(dfs))

    # Display column selection for each DataFrame
    for i, (df, col, name) in enumerate(zip(dfs, cols, df_names)):
        with col:
            st.subheader(f"📄 {name}")
            merge_columns[f"df{i}"] = st.selectbox(
                f"Select merge column",
                options=df.columns.tolist(),
                key=f"merge_col_{i}",
                help=f"Choose the column from {name} to use for merging"
            )
            st.caption(f"Total columns: {len(df.columns)}")

    # Merge settings
    st.header("4. Merge Settings")
    merge_type = st.selectbox(
        "Choose how to handle rows that don't match across files:",
        options=['outer', 'inner', 'left', 'right'],
        help="""
        - Outer: Keep all rows from all files (recommended)
        - Inner: Keep only rows that exist in all files
        - Left: Keep all rows from the first file
        - Right: Keep all rows from the second file
        """
    )

    # Merge preview section with progress tracking
    st.header("5. Preview Merged Data")

    if st.button("🔄 Generate Preview", help="Click to preview the merged data"):
        with st.spinner("Merging files..."):
            try:
                merged_df, merge_stats = merge_dataframes(dfs, merge_columns, selected_columns, df_names, merge_type)
                st.write("Preview of merged data (first 5 rows):")
                st.dataframe(merged_df.head(), use_container_width=True)

                # Display merge statistics
                st.subheader("📊 Merge Statistics")
                cols = st.columns(3)
                with cols[0]:
                    st.metric("📈 Total Rows in Original Files", 
                            f"{merge_stats['total_rows_original']:,}")
                with cols[1]:
                    st.metric("📊 Rows After Merge", 
                            f"{merge_stats['total_rows_merged']:,}")
                with cols[2]:
                    st.metric("📑 Files Merged", len(dfs))

                # Display new/missing rows statistics
                st.subheader("🔄 Row Matching Statistics")
                for i in range(1, len(dfs)):
                    st.info(f"""
                    File {i+1} ({df_names[i]}):
                    - New rows: {merge_stats['new_rows_per_file'][i]:,}
                    - Missing rows: {merge_stats['missing_rows_per_file'][i]:,}
                    """)

                # Download section with format options
                st.header("6. Download Merged File")
                download_format = st.radio(
                    "Select download format:",
                    options=['csv', 'xlsx'],
                    horizontal=True,
                    help="Choose the format for your merged file"
                )

                buffer, mime = get_download_buffer(merged_df, download_format)

                st.download_button(
                    label="⬇️ Download merged file",
                    data=buffer,
                    file_name=f"merged_data.{download_format}",
                    mime=mime,
                    help="Click to download the merged file"
                )

            except ValueError as e:
                st.error(f"❌ Merge Error: {str(e)}")
            except Exception as e:
                st.error(f"❌ An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()