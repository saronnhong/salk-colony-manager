export interface AuditOperation {
  id: number;
  operation_type: 'animal_move' | 'cage_move' | string;
  performed_by: number;
  performed_by_name: string;
  performed_at: string;
  reason: string;
  metadata: Record<string, unknown>;
  reverses_operation: number | null;
  is_reversed: boolean;
  can_undo: boolean;
}