export type HusbandryEventType =
  | 'intake'
  | 'cage_change'
  | 'health_check'
  | 'weight'
  | 'treatment'
  | 'death'
  | 'transfer'
  | 'weaning'
  | 'tail_snip';

export interface HusbandryTreatmentDetail {
  drug_name: string;
  dose: string;
  route: string;
}

export interface HusbandryEvent {
  id: number;
  event_type: HusbandryEventType;
  animal: string | null;
  cage: string | null;
  litter: string | null;
  event_datetime: string;
  recorded_at: string;
  recorded_by: number | null;
  recorded_by_name: string | null;
  notes: string;
  metadata: Record<string, unknown>;
  weight_grams: number | null;
  treatment: HusbandryTreatmentDetail | null;
}

export interface HusbandryEventCreateRequest {
  event_type: HusbandryEventType;
  animal?: string;
  cage?: string;
  litter?: string;
  event_datetime: string;
  notes?: string;
  metadata?: Record<string, unknown>;

  weight_grams?: number;

  treatment_name?: string;
  dose?: string;
  route?: string;
}