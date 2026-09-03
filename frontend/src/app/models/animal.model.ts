export interface AnimalLocation {
  cage_id: string;
  cage_code: string;
  valid_from: string;
}

export interface AnimalDetailModel {
  id: string;
  identifier: string | null;
  sex: string;
  date_of_birth: string | null;
  species: string;
  strain_name: string | null;
  retired_reason: string;
  retired_at: string | null;
  created_at: string;
  current_location: AnimalLocation | null;
}

export interface AnimalLocationHistory {
  id: number;
  cage_code: string;
  room: string | null;
  rack: string | null;
  position: string | null;
  valid_from: string;
  valid_to: string | null;
  system_from: string;
  system_to: string | null;
  reason: string;
}

export interface AnimalMoveRequest {
  destination_cage_id: string;
  moved_at?: string;
  reason?: string;
}