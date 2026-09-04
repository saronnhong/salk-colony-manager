export interface ImportRowPreview {
  id: number;
  row_number: number;
  raw_data: {
    local_id?: string;
    sex?: string;
    date_of_birth?: string;
    species?: string;
    strain?: string;
    cage_code?: string;
    [key: string]: unknown;
  };
  parse_status: 'valid' | 'invalid' | 'pending' | 'skipped' | 'committed';
  validation_errors: Record<string, string> | null;
}

export interface ImportBatchPreview {
  id: number;
  filename: string;
  uploaded_at: string;
  status:
    | 'uploaded'
    | 'validated'
    | 'validation_failed'
    | 'committed'
    | 'committed_with_errors'
    | 'undone';
  rows: ImportRowPreview[];
}

export interface ImportCommitResponse {
  batch: ImportBatchPreview;
  committed_count: number;
  skipped_count: number;
}